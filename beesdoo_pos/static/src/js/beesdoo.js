odoo.define("beesdoo_pos.screens", function (require) {
    "use strict";
    var screens = require("point_of_sale.screens");
    var models = require("point_of_sale.models");

    models.load_fields("res.partner", "is_company");

    var set_customer_info = function (el_class, value, prefix) {
        var el = this.$(el_class);
        el.empty();
        if (prefix && value) {
            value = prefix + value;
        }
        if (value) {
            el.append(value);
        }
    };

    screens.ActionpadWidget.include({
        renderElement: function () {
            var self = this;
            var loaded = new $.Deferred();
            this._super();
            if (!this.pos.get_client()) {
                return;
            }
            var customer_id = this.pos.get_client().id;
            this._rpc(
                {
                    model: "res.partner",
                    method: "get_eater",
                    args: [customer_id],
                },
                {
                    shadow: true,
                },
                {
                    timeout: 1000,
                }
            )
                .then(function (result) {
                    for (let i = 0; i < result.length; i++) {
                        set_customer_info.call(
                            self,
                            ".customer-delegate".concat(i + 1),
                            result[i],
                            "Eater".concat(i + 1, ": ")
                        );
                    }
                })
                .fail(function (type, error) {
                    loaded.reject(error);
                });
        },
    });

    screens.PaymentScreenWidget.include({
        render_customer_info: function () {
            var self = this;
            var loaded = new $.Deferred();
            if (!this.pos.get_client()) {
                return;
            }
            var customer_id = this.pos.get_client().id;
            this._rpc(
                {
                    model: "res.partner",
                    method: "get_eater",
                    args: [customer_id],
                },
                {
                    shadow: true,
                },
                {
                    timeout: 1000,
                }
            )
                .then(function (result) {
                    set_customer_info.call(
                        self,
                        ".customer-name",
                        self.pos.get_client().name
                    );
                    for (let i = 0; i < result.length; i++) {
                        set_customer_info.call(
                            self,
                            ".customer-delegate".concat(i + 1),
                            result[i],
                            "Eater".concat(i + 1, ": ")
                        );
                    }
                })
                .fail(function (type, error) {
                    loaded.reject(err);
                });
        },

        auto_invoice: function () {
            var self = this;
            var customer = this.pos.get_client();
            var order = this.pos.get_order();
            if (customer && customer.is_company && !order.is_to_invoice()) {
                self.click_invoice();
            }
            if (!customer && order.is_to_invoice()) {
                self.click_invoice();
            }
        },

        renderElement: function () {
            this._super();
            this.render_customer_info();
        },

        customer_changed: function () {
            this._super();
            if (this.pos.config.module_account) {
                this.auto_invoice();
            }
            this.render_customer_info();
        },
    });
});
