require([
    'jquery',
    'loki',
    'util/datatables',
    'asset-util',
], function($, loki, datatables, asset_util) {
    loki.configure({
        sidebar: undefined
    });

    // Constants
    var right_pane_width = '30%';

    var decode_uri = function(x) {
        x = x.replace(/\+/g, '%20'); // 'Friday%20September%2013th'
        x = decodeURIComponent(x);   // 'Friday September 13th'
        return x;
    };

    loki.ready(function() {
        console.log('asset.js loaded');

        $('.search-input > form > input').on('keyup', function(e) {
            var $this = $(this),
                text = $(this).val();
            console.log('keyup', text);

            if ($this.val()) {
                $this.trigger('receive-input');
            } else {
                $this.trigger('clear-input');
            }
        }).on('receive-input', function(e, text) {
            if (text)
                $(this).val(text);
            $('.search-input > .close-button').css('opacity', '1');
        }).on('clear-input', function(e, reset) {
            if (reset)
                $(this).val('');
            $('.search-input > .close-button').css('opacity', '0');
        });

        $('.search-input > form').on('submit', function(e) {
            e.preventDefault();
            var text = $(this).find('> input').val();
            console.log('submit', text);

            if (text) {
                loki.route_params({search: text});
            } else {
                loki.route_params({search: undefined});
            }
        });

        // Input close (clear) button
        $('.search-input .close-button').on('click', function() {
            $('.search-input > form > input').trigger('clear-input');
            loki.route_params({search: undefined});
        });

        // Right pane close button
        $('.right-pane .close-button').on('click', function() {
            toggleRightPane(false);
        });

        // Create template table
        var tableOptions = {
                // Must return: sn, hostname, type
                columns: [
                    {data: 'hostname'},
                    {
                        data: 'status',
                        render: function(data, type, full, meta) {
                            if (data == 'online') {
                                return '<span style="color: green">' + data + '</span>';
                            } else {
                                return '<span style="color: red">' + data + '</span>';
                            }
                        }
                    },
                    {
                        data: 'private_ip',
                        render: function(data, type, full, meta) {
                            var ips,
                                ips_html;
                            if (data === undefined)
                                ips = [];
                            if ($.isArray(data))
                                ips = data;
                            else
                                ips = [];
                            if (ips.length) {
                                ips_html = '';
                                ips.forEach(function(ip) {
                                    ips_html += '<span>' + ip + '</span>';
                                });
                            } else {
                                ips_html = '<i>null</i>';
                            }
                            return '<div class="cell-private-ip">' + ips_html + '</div>';
                        }
                    },
                    {data: 'type'},
                    {data: 'idc', defaultContent: '<i>null</i>'},
                    {data: 'sn'},
                ],
                scrollY: (window.innerHeight - 250) + 'px',
                scrollCollapse: false,
                autoWidth: false,
                tableTools: {
                    "sRowSelect": "single",  // or 'multi'
                }
            },
            serverTable = datatables.createDataTable(
                $('.server-table'), tableOptions);
        loki.serverTable = serverTable;

        $('.server-table').on('click row_select', 'tr', function() {
            var selected = serverTable.rows('.selected').data()[0];
            console.log(selected);

            if (selected) {
                toggleRightPane(true);

                asset_util.renderServerDetail(
                    selected.sn,
                    $('.right-pane .server-detail')
                );
            }
        });
    });


    loki.defineParamsHandler(function(params) {
        console.log('get params', params);

        // var search_text = decode_uri(params.search);
        var search_text = params.search;
        if (search_text) {
            // Fill in input
            $('.search-input > form > input').trigger('receive-input', search_text);

            showSearchResult(search_text);
        } else {
            // Clear input
            $('.search-input > form > input').trigger('clear-input', true);

            // Clear datatable
            loki.serverTable.clearData();

            showDashboard();
        }
    });


    var searchServers = function(text) {
        $.ajax({
            url: '/api/asset/query',
            data: {
                fuzzy_word: text
            },
            success: function(data) {
                var dt = loki.serverTable;

                dt.reloadData(data);
            }
        });
    };


    var showSearchResult = function(text) {
        $('.dashboard').hide();
        $('.asset-main').show();
        $('.search-result').show();

        searchServers(text);
    };


    var showDashboard = function() {
        $('.search-result').hide();
        $('.asset-main').show();
        $('.dashboard').show();
    };


    var toggleRightPane = function(flag) {
        if (flag) {
            $('.right-pane').addClass('opened');
        } else {
            $('.right-pane').removeClass('opened');
        }
    };


    loki.run();
});
