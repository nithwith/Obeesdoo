import logging
import math
from datetime import datetime, time, timedelta

from pytz import UTC, timezone

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


def float_to_time(f):
    decimal, integer = math.modf(f)
    return "{}:{}".format(
        str(int(integer)).zfill(2), str(int(round(decimal * 60))).zfill(2)
    )


def floatime_to_hour_minute(f):
    decimal, integer = math.modf(f)
    return int(integer), int(round(decimal * 60))


def get_first_day_of_week():
    today = datetime.now()
    return (datetime.now() - timedelta(days=today.weekday())).date()


class ShiftType(models.Model):
    _name = "shift.type"
    _description = "shift.type"

    name = fields.Char()
    description = fields.Text()
    active = fields.Boolean(default=True)


class ShiftDayNumber(models.Model):
    _name = "shift.daynumber"
    _description = "shift.daynumber"

    _order = "number asc"

    name = fields.Char()
    number = fields.Integer(
        "Day Number",
        help="From 1 to N, When you will instanciate your planning, Day 1 "
        "will be the start date of the instance, Day 2 the second, "
        "etc...",
    )
    active = fields.Boolean(default=True)


class ShiftPlanning(models.Model):
    _name = "shift.planning"
    _description = "shift.planning"
    _order = "sequence asc"

    sequence = fields.Integer()
    name = fields.Char()
    periodicity = fields.Integer(
        help="""From 1 to N. This number specifies the periodicity for the
        automated generation of a planning. For a weekly planning, the
        periodicity would be 7, because the planning has to be generated
        every seven days.""",
        default=7,
    )
    task_template_ids = fields.One2many("shift.template", "planning_id")

    @api.model
    def _get_next_planning(self, sequence):
        """There can be multiple planning templates defined. When
        generating shifts automatically, one template has to be
        selected. The sequence number of the previously used
        template is stored, so that it can be bumped up in a
        cyclic fashion."""
        next_planning = self.search([("sequence", ">", sequence)])
        if not next_planning:
            return self.search([])[0]
        return next_planning[0]

    def _get_next_planning_date(self, date):
        self.ensure_one()
        periodicity = self.periodicity
        if not periodicity:
            raise ValueError(
                """Template periodicity is undefined although it
                should have the default value or a value given by
                the user."""
            )
        return date + timedelta(days=periodicity)

    @api.model
    def _generate_next_planning(self):
        config = self.env["ir.config_parameter"].sudo()
        last_seq = int(config.get_param("shift.last_planning_seq", 0))
        date = fields.Date.from_string(config.get_param("shift.next_planning_date", 0))

        planning = self._get_next_planning(last_seq)
        planning = planning.with_context(visualize_date=date)

        if not planning.task_template_ids:
            _logger.error("Could not generate next planning: no task template defined.")
            return

        planning.task_template_ids.generate_task_day()

        next_date = planning._get_next_planning_date(date)
        config.set_param("shift.last_planning_seq", planning.sequence)
        config.set_param("shift.next_planning_date", next_date)

    @api.model
    def get_future_shifts(
        self,
        end_date,
        start_date=None,
        include_cancelled=True,
    ):
        """
        Calculates shifts between start_date and end_date without
        storing them in the database.
        Uses a list of shifts instead of a recordset because
        of issues occuring when copying records.
        :param end_date: Datetime
        :return: shift.shift list
        """
        if not start_date:
            start_date = datetime.now()
        # Getting existing shifts
        shift_domain = [("start_time", ">", start_date.strftime("%Y-%m-%d %H:%M:%S"))]
        if not include_cancelled:
            shift_domain.append(("state", "!=", "cancel"))

        existing_shift_list = list(
            self.env["shift.shift"]
            .sudo()
            .search(
                shift_domain,
                order="start_time, task_template_id, task_type_id",
            )
        )

        # Getting parameters
        last_sequence = int(
            self.env["ir.config_parameter"].sudo().get_param("shift.last_planning_seq")
        )

        next_planning = self._get_next_planning(last_sequence)

        next_planning_date = fields.Datetime.from_string(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("shift.next_planning_date", 0)
        )

        next_planning = next_planning.with_context(visualize_date=next_planning_date)

        # The following loop will generate a list of shifts. Each shift
        # is a dictionary. The conversion to a recordset is performed
        # after filtering the new shift to avoid unnecessary
        # computations.
        future_shift_list = []
        while next_planning_date < end_date:
            for shift in next_planning.task_template_ids._prepare_task_day():
                if shift["start_time"] > start_date:
                    future_shift_list.append(shift)
            next_planning_date = next_planning._get_next_planning_date(
                next_planning_date
            )
            last_sequence = next_planning.sequence
            next_planning = self._get_next_planning(last_sequence)
            next_planning = next_planning.with_context(
                visualize_date=next_planning_date
            )

        # Filtering future shifts
        filtered_future_shift_list = future_shift_list

        # Converting dictionary to recordset
        shift_list = existing_shift_list + [
            self.env["shift.shift"].new(shift) for shift in filtered_future_shift_list
        ]

        return shift_list


class ShiftTemplate(models.Model):
    _name = "shift.template"
    _description = "shift.template"
    _order = "start_time"

    name = fields.Char(required=True)
    planning_id = fields.Many2one("shift.planning", required=True)
    day_nb_id = fields.Many2one("shift.daynumber", string="Day", required=True)
    task_type_id = fields.Many2one("shift.type", string="Type")
    start_time = fields.Float(required=True)
    end_time = fields.Float(required=True)

    duration = fields.Float(help="Duration in Hour")
    worker_nb = fields.Integer(
        string="Number of worker",
        help="Max number of worker for this task",
        default=1,
    )
    active = fields.Boolean(default=True)
    # For Kanban View Only
    color = fields.Integer("Color Index")
    # For calendar View
    start_date = fields.Datetime(compute="_compute_fake_date", search="_search_dummy")
    end_date = fields.Datetime(compute="_compute_fake_date", search="_search_dummy")

    def _get_utc_date(self, day, hour, minute):
        """Combine day number, hours and minutes to save
        corresponding UTC datetime in database.
        """
        context_tz = timezone(self._context.get("tz") or self.env.user.tz)
        day_local_time = datetime.combine(day, time(hour=hour, minute=minute))
        day_local_time = context_tz.localize(day_local_time)
        day_utc_time = day_local_time.astimezone(UTC)
        # Return naïve datetime so as to be saved in database
        return day_utc_time.replace(tzinfo=None)

    @api.depends("start_time", "end_time")
    @api.depends_context("visualize_date")
    def _compute_fake_date(self):
        today = self._context.get("visualize_date", get_first_day_of_week())
        for rec in self:
            # Find the day of this task template 'rec'.
            day = today + timedelta(days=rec.day_nb_id.number - 1)
            # Compute the beginning and ending time according to the
            # context timezone.
            h_begin, m_begin = floatime_to_hour_minute(rec.start_time)
            h_end, m_end = floatime_to_hour_minute(rec.end_time)
            rec.start_date = self._get_utc_date(day, h_begin, m_begin)
            rec.end_date = self._get_utc_date(day, h_end, m_end)

    def _search_dummy(self, operator, value):
        return []


    @api.onchange("start_time", "end_time")
    def _get_duration(self):
        if self.start_time and self.end_time:
            self.duration = self.end_time - self.start_time

    @api.onchange("duration")
    def _set_duration(self):
        if self.start_time:
            self.end_time = self.start_time + self.duration

    def _prepare_task_day(self):
        """
        Generates a list of dict objects containing the informations
        for the shifts to generate based on the template data
        """
        tasks = []
        for rec in self:
            for i in range(0, rec.worker_nb):
                tasks.append(
                    {
                        "name": "[%s] %s %s (%s - %s) [%s]"
                        % (
                            rec.start_date.date(),
                            rec.planning_id.name,
                            rec.day_nb_id.name,
                            float_to_time(rec.start_time),
                            float_to_time(rec.end_time),
                            i,
                        ),
                        "task_template_id": rec.id,
                        "task_type_id": rec.task_type_id.id,
                        "start_time": rec.start_date,
                        "end_time": rec.end_date,
                        "state": "open",
                    }
                )

        return tasks

    def get_task_day(self):
        """
        Creates the shifts according to the template without saving
        them into the database.
        To adapt the behaviour, function _prepare_task_day()
        should be overwritten.
        """
        tasks = self.env["shift.shift"]
        task_list = self._prepare_task_day()
        for task in task_list:
            tasks |= tasks.new(task)
        return tasks

    def generate_task_day(self):
        """
        Creates the shifts according to the template and saves
        them into the database.
        To adapt the behaviour, function _prepare_task_day()
        should be overwritten.
        """
        tasks = self.env["shift.shift"]
        task_list = self._prepare_task_day()
        for task in task_list:
            tasks |= tasks.create(task)
        return tasks




