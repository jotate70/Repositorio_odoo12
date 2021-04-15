from odoo import fields, models, api, _
from odoo.exceptions import Warning
from datetime import date, datetime
import calendar
from dateutil.relativedelta import relativedelta
import logging
_logger = logging.getLogger(__name__)



YEARS = []
for year in range(int(date.today().strftime('%Y')) - 1 , int(date.today().strftime('%Y')) + 10):
   YEARS.append((str(year), str(year)))

PERIOD = [('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'), ('05', 'May'),
          ('06', 'June'), ('07', 'July'), ('08', 'August'), ('09', 'September'), ('10', 'October'),
          ('11', 'November'), ('12', 'December')]


class payslip_page_label_design(models.Model):
    _name = 'payslip.page.label.design'

    @api.model
    def default_get(self, fields_list):
        res = super(payslip_page_label_design, self).default_get(fields_list)
        for wiz in self.env['wizard.dynamic.payslip'].search([], order="id desc", limit=1):
            res.update({'page_template_design': wiz.column_report_design,
                        'report_model': wiz.report_model,
                        'margin_top': wiz.margin_top,
                        'margin_left': wiz.margin_left, 'margin_bottom': wiz.margin_bottom,
                        'margin_right': wiz.margin_right, 'orientation': wiz.orientation,
                })
        return res

    name = fields.Char(string="Design Name")
    report_model = fields.Char(string='Model')
    page_template_design = fields.Text(string="Report Design")
    # page
    dpi = fields.Integer(string='DPI', default=80, help="The number of individual dots\
                                that can be placed in a line within the span of 1 inch (2.54 cm)")
    margin_top = fields.Integer(string='Margin Top (mm)', default=1)
    margin_left = fields.Integer(string='Margin Left (mm)', default=1)
    margin_bottom = fields.Integer(string='Margin Bottom (mm)', default=1)
    margin_right = fields.Integer(string='Margin Right (mm)', default=1)
    orientation = fields.Selection([('Landscape', 'Landscape'),
                                    ('Portrait', 'Portrait')],
                                   string='Orientation', default='Portrait', required=True)
    # new columns and rows fields
    format = fields.Selection([('A0', 'A0  5   841 x 1189 mm'),
                                ('A1', 'A1  6   594 x 841 mm'),
                                ('A2', 'A2  7   420 x 594 mm'),
                                ('A3', 'A3  8   297 x 420 mm'),
                                ('A4', 'A4  0   210 x 297 mm, 8.26 x 11.69 inches'),
                                ('A5', 'A5  9   148 x 210 mm'),
                                ('A6', 'A6  10  105 x 148 mm'),
                                ('A7', 'A7  11  74 x 105 mm'),
                                ('A8', 'A8  12  52 x 74 mm'),
                                ('A9', 'A9  13  37 x 52 mm'),
                                ('B0', 'B0  14  1000 x 1414 mm'),
                                ('B1', 'B1  15  707 x 1000 mm'),
                                ('B2', 'B2  17  500 x 707 mm'),
                                ('B3', 'B3  18  353 x 500 mm'),
                                ('B4', 'B4  19  250 x 353 mm'),
                                ('B5', 'B5  1   176 x 250 mm, 6.93 x 9.84 inches'),
                                ('B6', 'B6  20  125 x 176 mm'),
                                ('B7', 'B7  21  88 x 125 mm'),
                                ('B8', 'B8  22  62 x 88 mm'),
                                ('B9', 'B9  23  33 x 62 mm'),
                                ('B10', ':B10    16  31 x 44 mm'),
                                ('C5E', 'C5E 24  163 x 229 mm'),
                                ('Comm10E', 'Comm10E 25  105 x 241 mm, U.S. '
                                 'Common 10 Envelope'),
                                ('DLE', 'DLE 26 110 x 220 mm'),
                                ('Executive', 'Executive 4   7.5 x 10 inches, '
                                 '190.5 x 254 mm'),
                                ('Folio', 'Folio 27  210 x 330 mm'),
                                ('Ledger', 'Ledger  28  431.8 x 279.4 mm'),
                                ('Legal', 'Legal    3   8.5 x 14 inches, '
                                 '215.9 x 355.6 mm'),
                                ('Letter', 'Letter 2 8.5 x 11 inches, '
                                 '215.9 x 279.4 mm'),
                                ('Tabloid', 'Tabloid 29 279.4 x 431.8 mm'),
                                ('custom', 'Custom')],
                               string='Paper Type', default="custom",
                               help="Select Proper Paper size")
    active = fields.Boolean(string="Active", default=True)


    

class wizard_dynamic_payslip(models.TransientModel):
    _name = "wizard.dynamic.payslip"

    @api.model
    def _get_report_paperformat_id(self):
        xml_id = self.env['ir.actions.report'].search([('report_name', '=',
                                                        'dynamic_product_page_label.dynamic_prod_page_rpt')])
        if not xml_id or not xml_id.paperformat_id:
            raise Warning('Someone has deleted the reference paper format of report.\
                Please Update the module!')
        return xml_id.paperformat_id.id
    
    @api.onchange('paper_format_id')
    def onchange_report_paperformat_id(self):
        if self.paper_format_id:
            self.format = self.paper_format_id.format
            self.orientation = self.paper_format_id.orientation
            self.margin_top = self.paper_format_id.margin_top
            self.margin_left = self.paper_format_id.margin_left
            self.margin_bottom = self.paper_format_id.margin_bottom
            self.margin_right = self.paper_format_id.margin_right
            self.dpi = self.paper_format_id.dpi

    @api.onchange('design_id')
    def on_change_design_id(self):
        if self.design_id:
            self.column_report_design = self.design_id.page_template_design
            self.report_model = self.design_id.report_model
            # paper format args
            self.format = self.design_id.format
            self.orientation = self.design_id.orientation
            self.dpi = self.design_id.dpi
            self.margin_top = self.design_id.margin_top
            self.margin_left = self.design_id.margin_left
            self.margin_bottom = self.design_id.margin_bottom
            self.margin_right = self.design_id.margin_right

    @api.multi
    @api.onchange('dpi')
    def onchange_dpi(self):
        if self.dpi < 80:
            self.dpi = 80


    department_ids = fields.Many2many('hr.department',
                                      'hr_emp_department_rel',
                                      'emp_id', 'dept_id', string="Departments")
    employee_ids = fields.Many2many('hr.employee',
                                    'hr_emp_dynamic_payslip_rel',
                                    'emp_id', 'payslip_id' , string="Employee")
    from_month = fields.Selection(PERIOD, string="From Month", default=date.today().strftime('%m'))
    from_year = fields.Selection(YEARS, string="From Year", default=date.today().strftime('%Y'))
    to_month = fields.Selection(PERIOD, string="To Month", default=(date.today() + relativedelta(months=1)).strftime('%m'))
    
    to_year = fields.Selection(YEARS, string="From Year", default=date.today().strftime('%Y'))
    
    dpi = fields.Integer(string='DPI', default=80, help="The number of individual dots \
                        that can be placed in a line within the span of 1 inch (2.54 cm)")
    margin_top = fields.Integer(string='Margin Top (mm)', default=1)
    margin_left = fields.Integer(string='Margin Left (mm)', default=1)
    margin_bottom = fields.Integer(string='Margin Bottom (mm)', default=1)
    margin_right = fields.Integer(string='Margin Right (mm)', default=1)
    header_spacing = fields.Integer(string="Header spacing", default=35)
    orientation = fields.Selection([('Landscape', 'Landscape'),
                                    ('Portrait', 'Portrait')],
                                    string='Orientation', default='Portrait')
    
    watermark_type = fields.Selection([('text', 'Text'),
                                       ('image', 'Image')], default="text")
    watermark_text = fields.Char(string="Watermark Text")
    watermark_image = fields.Binary(string="Watermark Image")
    design_id = fields.Many2one('payslip.page.label.design', string="Template")
    column_report_design = fields.Text(string="Design")
    report_model = fields.Char(string="Model")
    
    # report design
    # new columns and rows fields
    format = fields.Selection([('A0', 'A0  5   841 x 1189 mm'),
                                ('A1', 'A1  6   594 x 841 mm'),
                                ('A2', 'A2  7   420 x 594 mm'),
                                ('A3', 'A3  8   297 x 420 mm'),
                                ('A4', 'A4  0   210 x 297 mm, 8.26 x 11.69 inches'),
                                ('A5', 'A5  9   148 x 210 mm'),
                                ('A6', 'A6  10  105 x 148 mm'),
                                ('A7', 'A7  11  74 x 105 mm'),
                                ('A8', 'A8  12  52 x 74 mm'),
                                ('A9', 'A9  13  37 x 52 mm'),
                                ('B0', 'B0  14  1000 x 1414 mm'),
                                ('B1', 'B1  15  707 x 1000 mm'),
                                ('B2', 'B2  17  500 x 707 mm'),
                                ('B3', 'B3  18  353 x 500 mm'),
                                ('B4', 'B4  19  250 x 353 mm'),
                                ('B5', 'B5  1   176 x 250 mm, 6.93 x 9.84 inches'),
                                ('B6', 'B6  20  125 x 176 mm'),
                                ('B7', 'B7  21  88 x 125 mm'),
                                ('B8', 'B8  22  62 x 88 mm'),
                                ('B9', 'B9  23  33 x 62 mm'),
                                ('B10', ':B10    16  31 x 44 mm'),
                                ('C5E', 'C5E 24  163 x 229 mm'),
                                ('Comm10E', 'Comm10E 25  105 x 241 mm, U.S. '
                                 'Common 10 Envelope'),
                                ('DLE', 'DLE 26 110 x 220 mm'),
                                ('Executive', 'Executive 4   7.5 x 10 inches, '
                                 '190.5 x 254 mm'),
                                ('Folio', 'Folio 27  210 x 330 mm'),
                                ('Ledger', 'Ledger  28  431.8 x 279.4 mm'),
                                ('Legal', 'Legal    3   8.5 x 14 inches, '
                                 '215.9 x 355.6 mm'),
                                ('Letter', 'Letter 2 8.5 x 11 inches, '
                                 '215.9 x 279.4 mm'),
                                ('Tabloid', 'Tabloid 29 279.4 x 431.8 mm'),
                                ('custom', 'Custom')],
                               string='Paper Type', default="custom",
                               help="Select Proper Paper size")
    paper_format_id = fields.Many2one('report.paperformat', string="Paper Format")

    @api.constrains('from_month', 'to_month', 'from_year', 'to_year')
    def _months_validation(self):
        if self.from_month and self.to_month and self.from_year and self.to_year:
            from_date_str = str(self.from_year) + "-" + self.from_month + "-01"
            to_date_str = str(self.to_year) + "-" + self.to_month + "-"\
                    + str(calendar.monthrange(int(self.to_year), int(self.to_month))[1])
            from_date = datetime.strptime(from_date_str, '%Y-%m-%d')
            to_date = datetime.strptime(to_date_str, '%Y-%m-%d')
            if from_date > to_date:
                raise Warning(_('Please enter valid Time Period.'))
            
            
    @api.multi
    def action_print(self):
        if (self.margin_top < 0) or (self.margin_left < 0) or \
            (self.margin_bottom < 0) or (self.margin_right < 0):
            raise Warning('Margin Value(s) for report can not be negative!')
        xml_id = self.env['ir.actions.report'].search([('report_name', '=',
                                                        'flexi_hr_ee.dynamic_payslip_report')])
        view_id = self.env['ir.ui.view'].search([('name', '=', 'dynamic_payslip_report'),
                                                 ('type', '=', 'qweb')], limit=1, order="id desc")
        if view_id and self.column_report_design:
            view_id.update({'arch_base': self.column_report_design})
        if self.design_id and self.column_report_design:
            self.design_id.update({'page_template_design': self.column_report_design})
        if self.paper_format_id:
            if self.format == 'custom':
                result = self.paper_format_id.sudo().write({
                                        'format': self.format,
                                        'orientation': self.orientation,
                                        'margin_top': self.margin_top,
                                        'margin_left': self.margin_left,
                                        'margin_bottom': self.margin_bottom,
                                        'margin_right': self.margin_right,
                                        'header_spacing': self.header_spacing,
                                        'dpi': self.dpi
                                    })
            else:
                result = self.paper_format_id.sudo().write({
                                        'format': self.format,
                                        'page_width': 0,
                                        'page_height': 0,
                                        'orientation': self.orientation,
                                        'margin_top': self.margin_top,
                                        'margin_left':self.margin_left,
                                        'margin_bottom': self.margin_bottom,
                                        'margin_right': self.margin_right,
                                        'header_spacing': self.header_spacing,
                                        'dpi': self.dpi
                                    })
        if xml_id and self.paper_format_id:
            xml_id.sudo().update({'paperformat_id': self.paper_format_id})
        data = self.read()[0]
        datas = {
            'ids': self._ids,
            'model': 'wizard.dynamic.payslip',
        }
        return self.env.ref('flexi_hr_ee.dynamic_payslip_report_aspl').report_action(self, data=datas)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: