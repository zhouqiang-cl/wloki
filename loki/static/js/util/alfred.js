define([
    'jquery',
    'mousetrap',
    'selectize',
    'util/builtin-extend'
], function($, Mousetrap) {
    var exports = {},

        alfred_enabled = false,

        alfred_el, selectize_obj,

        options_retriever;


    var is_enabled = exports.is_enabled = function() {
        return alfred_el !== undefined;
    },

    /*
    get_nodes_by_ptree_config = function() {
        var data = window.loki.$ptree.jstree(true)._model.data,
            ptree_config = window.loki.ptree_config,
            nodes = [];

        for (var key in data) {
            if (data.hasOwnProperty(key)) {
                var origin_node = data[key].original;
                if (origin_node === undefined)
                    continue;
                var include = ptree_config.levels.contains(origin_node.negative_level)
                            || ptree_config.levels.contains(origin_node.level);
                switch (ptree_config.mode) {
                    case "disable":
                        if (include) {
                            //console.debug("forbid", origin_node);
                        } else {
                            nodes.push(origin_node);
                        }
                        break;
                    case "enable":
                        if (include) {
                            nodes.push(origin_node);
                        } else {
                            //console.debug("forbid", origin_node);
                        }
                        break;
                    default:
                        nodes.push(origin_node);
                }
            }
        }
        // console.debug("alfred load nodes", nodes);
        return nodes;
    },
    */

    // exported funciton blow

    // TODO show latest chosen
    enable_alfred = exports.enable_alfred = function(el, retriever, select_callback) {
        console.info('[ alfred ] Enabling alfred');
        alfred_el = el;
        options_retriever = retriever;

        // Initialize selectize input
        alfred_el.find('.loading').hide();
        var $input = el.find('> input').selectize({
            options: options_retriever(),
            valueField: 'id',
            searchField: 'path',
            labelField: 'path',
            maxItems: 1,
            maxOptions: 10,
            create: false,
            render: {
                option: function(item, escape) {
                    return '<div>' +
                        item.path + '<span class="dropdown-node-id">' + item.id + '</span>' +
                    '</div>';
                }
            },
            onChange: function (value) {
                console.log('change value', value);
                if (!value)
                    return;
                select_callback(value);
                close_alfred();
            },
        });
        selectize_obj = $input[0].selectize;
        if (alfred_el.is(':visible'))
            selectize_obj.focus();

        // Bind cancel
        el.find('.cancel').on('click', function() {
            close_alfred();
        });

        // Bind keys
        Mousetrap.bind(['command+/', 'ctrl+/'], function() {
            toggle_alfred();
        });
        Mousetrap.bind(['esc'], function() {
            close_alfred();
        });
        alfred_enabled = true;

        // For DEBUG
        // toggle_alfred();
    },

    reload_alfred = exports.reload_alfred = function() {
        if (!alfred_enabled) return;
        selectize_obj.clearOptions();
        selectize_obj.addOption(options_retriever());
        selectize_obj.refreshOptions();
    },

    open_alfred = exports.open_alfred = function() {
        alfred_el.show();
        reload_alfred();
        if (selectize_obj)
            selectize_obj.focus();
    },

    close_alfred = exports.close_alfred = function() {
        alfred_el.hide();
    },

    toggle_alfred = exports.toggle_alfred = function() {
        if (alfred_el.is(':visible'))
            close_alfred();
        else
            open_alfred();
    };

    return exports;
});
