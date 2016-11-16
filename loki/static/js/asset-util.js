define([
    'jquery',
    'handlebars',
], function($, Handlebars) {
    // Handlebars helpers
    Handlebars.registerHelper('in_column', function(options) {
        var v = this.value;
        if (!$.isArray(v)) {
            v = [v];

        }
        v_html = '';
        v.forEach(function(i) {
            v_html += '<span>' + i + '</span>';
        });
        return new Handlebars.SafeString(v_html);
    });

    Handlebars.registerHelper('ifeq', function(v1, v2, options) {
        if(v1 === v2)
            return options.fn(this);
        return options.inverse(this);
    });

    Handlebars.registerHelper('label', function(key) {
        var rv = key;
        switch (key) {
            case 'manu':
                rv = '制造商 (manu)';
                break;
            case 'mem':
                rv = '内存 (mem)';
                break;
            default:
                break;
        }
        return rv;
    });


    var exports = {},

        server_detail_template = Handlebars.compile($('#server-detail-template').html()),

        server_detail_basic_keys = ['sn', 'hostname', 'type'],

        server_detail_extended_excludes = ['vm_host', 'vm_name', 'vms'],

        renderServerDetail = exports.renderServerDetail = function(sn, container) {
            $.ajax({
                url: '/api/asset/detail/' + sn,
                success: function(data) {
                    // $('.right-pane')

                    var o = {
                        basic: {},
                        nodes: data.on_nodes,
                        extended: [],
                        others: {},
                        hidden: [],
                    };
                    delete data.on_nodes;
                    Object.keys(data).forEach(function(i) {
                        if (server_detail_basic_keys.indexOf(i) === -1) {
                            if (i.slice(0, 1) == '_') {
                                o.hidden.push({
                                    key: i,
                                    value: data[i],
                                });
                            } else {
                                if (server_detail_extended_excludes.indexOf(i) === -1) {
                                    o.extended.push({
                                        key: i,
                                        value: data[i],
                                    });
                                } else {
                                    o.others[i] = data[i];
                                }
                            }
                        } else {
                            o.basic[i] = data[i];
                        }
                    });
                    console.log('detail', o);

                    container.html(server_detail_template(o));

                    container.find('.show-hidden-wrapper > a')
                        .html('Show ' + o.hidden.length + ' more hidden')
                        .on('click', function(e) {
                            e.preventDefault();
                            container.find('.hidden').show();
                        });
                }
            });
        };


    return exports;
});
