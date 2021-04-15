odoo.define('performance_evaluation_rating.chatter_hide', function(require) {
    "use strict";
    var rpc = require('web.rpc');
    var FormController = require('web.FormController');
    FormController.include({
        renderButtons: function() {
            var self = this;
            this._super.apply(this, arguments);
            if (self.modelName && self.modelName == "kra.evaluation"){
                rpc.query({
                    model: 'ir.config_parameter',
                    method: 'get_param',
                    args: ['performance_evaluation_rating.include_internal_msg'],
                }, {
                    async: false
                }).then(function(res) {
                    if (res) {
                        setTimeout(function (){
                            self.$el.find('.o_chatter.oe_chatter').show();
                        },0);
                    }
                    else{
                        setTimeout(function (){
                            self.$el.find('.o_chatter.oe_chatter').hide();
                        },0);
                    }
                });
            }
        }
    });
});