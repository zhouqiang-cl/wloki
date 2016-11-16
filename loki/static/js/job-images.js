require([
    'jquery',
    'loki',
    'util/datatables',
], function($, loki, datatables) {
    $(function() {
        $('.pure-table')
            .on('draw.dt', function() {
                console.log('draw dt');
                $('.pure-table').css('opacity', '1');
            })
            .DataTable({
                pageLength: 30
            });
    });
});
