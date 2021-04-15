odoo.define('performance_evaluation_rating.main', function (require) {
    "use strict";

    var FormRenderer = require('web.FormRenderer');
    var rpc = require('web.rpc');
    var session = require('web.session');

    FormRenderer.include({
        _renderHeaderButtons: function (node) {
            var self = this;
            var $buttons = $('<div>', {class: 'o_statusbar_buttons'});
            var evl_record = false;
            var evl_record_uid = false
            if(self.state.model == 'kra.evaluation'){
                var params = {
                    model : 'kra.evaluation',
                    method : 'find_evaluation',
                    args: [[self.state.data.id]],
                };
                rpc.query(params, {async : false}).then(function(record){
                if(record){
                    evl_record = record[0][0]
                    evl_record_uid = record[1]
                    }
                });
                var is_hr_manager = false;
                var params = {
                    model : 'kra.evaluation',
                    method : 'check_user_group',
                    args: ['hr.group_hr_manager'],
                };
                rpc.query(params, {async : false}).then(function(result){
                    if(result){
                        is_hr_manager = true;
                    }
                });
                session.user_has_group('hr.group_hr_manager').then(function(result){
                    if(result){
                        is_hr_manager = true;
                    }
                })
            }

            _.each(node.children, function (child) {
                if (child.tag === 'button') {
                    if(evl_record){
                        if((!evl_record.self_review && !evl_record.double_validation && evl_record.state == "draft")
                        || (evl_record.self_review && !evl_record.double_validation && evl_record.state == "submit")
                        || (evl_record.self_review && evl_record.double_validation && evl_record.state == "waiting" && is_hr_manager)
                        || (!evl_record.self_review && evl_record.double_validation && evl_record.state == "waiting" && is_hr_manager)){
                            if(child.attrs.name == 'action_first_approval'){
                                if (self.state.context.uid == evl_record_uid){
                                    $buttons.append(self._renderHeaderButton(child));
                                }
                                else{
                                    if (self.state.data.hr_manager_user_ids){
                                     _.each(self.state.data.hr_manager_user_ids.data, function(record){
                                        if (self.state.context.uid == record.data.id){
                                            $buttons.append(self._renderHeaderButton(child));
                                        }
                                        })
                                    }
                                    }
                            }
                        }
                        if((evl_record.self_review && !evl_record.double_validation && evl_record.state == "draft")
                        || (evl_record.self_review && evl_record.double_validation && evl_record.state == "draft")){
                            if(child.attrs.name == 'action_submit_manager'){
                                $buttons.append(self._renderHeaderButton(child));
                            }
                        }
                         if((!evl_record.self_review && evl_record.double_validation && evl_record.state == "draft")
                         || (evl_record.self_review && evl_record.double_validation && evl_record.state == "submit")){
                            if(child.attrs.name == 'action_second_approval'){
                                if (self.state.context.uid == evl_record_uid){
                                    $buttons.append(self._renderHeaderButton(child));
                                }
                                else{
                                    if (self.state.data.hr_manager_user_ids){
                                     _.each(self.state.data.hr_manager_user_ids.data, function(record){
                                        if (self.state.context.uid == record.data.id){
                                            $buttons.append(self._renderHeaderButton(child));
                                        }
                                        })
                                    }
                                    }
                            }
                        }
                    } else{
                        $buttons.append(self._renderHeaderButton(child));
                    }
                }
                if (child.tag === 'widget') {
                    $buttons.append(self._renderTagWidget(child));
                }
            });
            return $buttons;
        },
    })
});