odoo.define('o16_pos_sales.pos_sales_modal', function (require) {
  'use strict';

  const { Gui } = require('point_of_sale.gui');
  const { Modal } = require('web.Dialog'); // Requiere el uso del modal de la librería web

  Gui.include({
      start: function () {
          this._super.apply(this, arguments);
          // Asegúrate de que la acción 'open_modal_action' está registrada correctamente
          this.pos.add_action_callback('action_open_modal', this._open_modal.bind(this));
      },

      _open_modal: function () {
          new Modal(this, {
              title: "Exportar Ventas",
              size: 'medium',
              $content: $('<div>').text('Este es un modal de prueba para Exportar Ventas.'),
              buttons: [
                  { text: "Cerrar", close: true }
              ]
          }).open();
      }
  });
});
