define([
    'jstree',
], function(jstree) {
    var exports = {};

    var default_options = {
        core: {
            //animation: 0,
            check_callback: true,
            //themes: {stripes: true},
            data: null,
            multiple: false,
        },
        types: {
            default: {
                icon: 'fa fa-leaf',
            },
            root:{
                icon: 'fa fa-dot-circle-o',
            },
            bottom: {
                icon: 'fa fa-cubes'
            }
        },
        plugins: ['types', 'search', 'sort']
    };

    var create_jstree = exports.create_jstree = function(el, options, data, refresh_callback) {
        if (!options) {
            // Set default options
            options = default_options;
        }

        if (data)
            options.core.data = data;

        el.jstree(options);

        return el.jstree(true);
    };

    var update_jstree = exports.update_jstree = function(jstree, data, refresh_callback) {
        jstree.settings.core.data = reformatNodes(data);

        if (refresh_callback) {
            el.on('refresh.jstree', function () {
                refresh_callback()
                el.off('refresh.jstree');
            });
        }

        jstree.refresh();
    };



    return exports;
});