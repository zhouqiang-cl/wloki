define([
    'jquery',
    'pikaday'
], function($, Pikaday) {
    var exports = {};


    var render = exports.render = function($input, _options) {
        var picker = new Pikaday($.extend(true, {
            field: $input[0],
            format: 'YYYY-MM-DD',
            /* onSelect example:
            onSelect: function() {
                console.log(this.getMoment().format('Do MMMM YYYY'));
            }
            */
        }, _options));
        $input.data('timepicker', picker);
        return picker;
    };


    return exports;
});
