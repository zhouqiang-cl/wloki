require([
    'jquery',
    'asset-util',
], function($, asset_util) {

    $(function() {
        asset_util.renderServerDetail(
            $('input[name=sn]').val(),
            $('.server-detail')
        );
    });
});
