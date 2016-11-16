define([
    'jquery',
    'util/jsform',
    'util/jstree',
], function($, jsform, jstree) {

    jsform.registerCustomType('servers_checkbox', {
    //jsform.registerCustomType('servers_checkbox', {
        template: '<div class="form-row" data-key="{{key}}" data-type="servers_checkbox">' +
            '<label>{{label}}</label>' +
            '<div class="tree"></div>' +
            '<div class="selected-servers"></div>' +
            '<div class="selected-servers-stat"></div>' +
            '</div>',

        processor: function(row, raw_data) {
            var data = raw_data.value;
            // Create jstree
            var tree = row.find('.tree'),
                tree_ins = jstree.create_jstree(
                    tree,
                    {
                        core: {
                            //animation: 0,
                            check_callback: true,
                            //themes: {stripes: true},
                            data: null,
                            multiple: true,
                        },
                        types: {
                            default: {
                                icon: false
                            },
                            server: {
                                icon: 'fa fa-server server-checkbox-icon'
                            }
                        },
                        plugins: ['types', 'checkbox', 'sort']
                    },
                    data
                ),
                container = row.find('.selected-servers'),
                stat = row.find('.selected-servers-stat'),
                // Function
                serialize_row = this.serializer.bind(this, row);

            // Open jstree
            tree.on('ready.jstree', function() {
                var root_node = tree_ins.get_node('#').children[0];
                tree_ins.open_node(root_node);
                // TREE_INS = tree_ins;
                /*
                var has_child = {},
                    idc_node;
                data.forEach(function(i) {
                    if (i.type == 'server')
                        return;
                    if (i.parent == '#') {
                        has_child[i.id] = 1;
                    } else {
                        has_child[i.parent] = 1;
                    }
                });

                tree_ins.open_all();
                data.forEach(function(i) {
                    if (i.type == 'server' || has_child[i.id])
                        return;
                    idc_node = tree_ins.get_node(i.id);
                    tree_ins.close_node(tree_ins.get_parent(idc_node));
                });
                // TREE = tree_ins;

                */
                tree.off('ready.jstree');
                _show_servers();
            });

            // Show servers on select/deselect
            var _show_servers = function () {
                // console.log('serialize_row', serialize_row());

                var selected = serialize_row(),
                    idcs = {},
                    get_tab_id = function (idc) {
                        return 'servers-tab-' + idc;
                    },
                    get_ul_id = function (idc) {
                        return 'servers-ul-' + idc;
                    };

                container.empty();

                // Insert servers
                selected.forEach(function (server) {
                    var idc = server.split('.')[1],
                        idc_div,
                        tab, ul;

                    if (idcs[idc] === undefined) {
                        // Create & append tab & ul
                        tab = $('<div></div>')
                            .addClass('servers-tab').attr('id', get_tab_id(idc));
                        ul = $('<ul></ul>')
                            .addClass('servers-ul').attr('id', get_ul_id(idc));
                        idc_div = $('<div></div>')
                            .addClass('idc')
                            .append(tab).append(ul);
                        container.append(idc_div);

                        idcs[idc] = {
                            tab: tab,
                            ul: ul,
                            count: 1
                        };
                    } else {
                        idcs[idc].count += 1;

                        // Get ul
                        ul = idcs[idc].ul;
                    }

                    var server_item = $('<li></li>').html(server);
                    ul.append(server_item);
                });

                // Update stat
                var sum = 0;
                for (var idc in idcs) {
                    var idc_obj = idcs[idc];
                    tab = idc_obj.tab;
                    tab.html(idc + '(' + idc_obj.count + ')');
                    sum += idc_obj.count;
                }
                stat.html('Total selected: ' + sum);
            };
            tree.on('select_node.jstree deselect_node.jstree', _show_servers);
        },

        serializer: function(row) {
            var tree = row.find('.tree'),
                tree_ins = tree.jstree(true),
                set = {};
            tree_ins.get_selected(true).forEach(function(i) {
                if (i.type == 'server') {
                    set[i.original.hostname] = true;
                }
            });
            data = Object.keys(set);
            return data;
        }
    });

});
