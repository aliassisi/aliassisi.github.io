let TableCSV = function( $scope, $ ){
    var section_id = $scope.data('id'),
        wrapper_id = '#tablentor-table-csv-'+section_id,
        tableWrapper = $(wrapper_id);
        table_id = $(wrapper_id + ' .tablentor-table-csv');
        options = tableWrapper.data('table');        

    if ( ! options ) {
        return;
    }

    options = JSON.parse( atob(options) );

    if ( ! options.table || 'yes' !== options.table ) {
        return;
    }

    new DataTable(table_id, {
        paging: 'yes' === options?.paging,
        ordering: 'yes' === options?.ordering,
        searching: 'yes' === options?.searching,
        initComplete: function(){
            tableWrapper.addClass('data-table-initialized');
            if ( 'yes' !== options?.paging ) {
                $(table_id).find('.dt-info').remove();
            }

            if ( 'no' === options?.paging_length ) {
                tableWrapper.find('.dt-length').remove();
            }
        }
    });
}

jQuery(window).on("elementor/frontend/init", function () {
	elementorFrontend.hooks.addAction("frontend/element_ready/tablentor-table-csv.default", TableCSV);
});
  