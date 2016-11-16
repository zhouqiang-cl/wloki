define([
    'underscore',
    'jquery',
    'loki',
    'util/datatables'
], function(_, $, loki, datatables) {
    var exports = {};

    /* OOP Helper */
    var __class_extend = function(protoProps, staticProps) {
        var parent = this;
        var child;
        // The constructor function for the new subclass is either defined by you
        // (the "constructor" property in your `extend` definition), or defaulted
        // by us to simply call the parent's constructor.
        if (protoProps && _.has(protoProps, 'constructor')) {
            child = protoProps.constructor;
        } else {
          child = function(){ return parent.apply(this, arguments); };
        }
        // Add static properties to the constructor function, if supplied.
        _.extend(child, parent, staticProps);
        // Set the prototype chain to inherit from `parent`, without calling
        // `parent`'s constructor function.
        var Surrogate = function(){ this.constructor = child; };
        Surrogate.prototype = parent.prototype;
        child.prototype = new Surrogate;
        // Add prototype properties (instance properties) to the subclass,
        // if supplied.
        if (protoProps) _.extend(child.prototype, protoProps);
        // Set a convenience property in case the parent's prototype is needed
        // later.
        child.__super__ = parent.prototype;
        return child;
    };


    var delegateEventSplitter = /^(\S+)\s*(.*)$/;


    /* Main class */
    /* Usage Example:
    var FooTabView = TabView.extend({
        tab_name: 'FooBar',
        ptree_config: {
            mode: 'disable',
            levels: []
        },
        $el: $('#tab-1'),
        events: {
        },
        initialize: function() {
        },
        handleParams: function(params) {
        },

        // For table & table item interaction
        $table: ,
        $table_search: ,
        table_options: {
        },
        fetchTableData: function(nid) {
        },
        afterRenderTable: function() {
        }
        onSelectRow: function(rid, item) {
        },
        onDeselectRow: function() {
        },
    })
    */

    var TabView = exports.TabView = function() {
        /*
         * Properties to assign:
         * - tab_name
         * - ptree_config
         * - $el
         * - events
         * - table_options
         * - table_selectable
         * - $table
         * - $table_search
         * Methods to define:
         * - initialize
         * - onSelectRow
         * - onDeselectRow
         */

        if (this.table_selectable === undefined)
            this.table_selectable = false;

        if (this.$table) {
            // Create dt instance
            var dt = this.table_dt = this._createDataTable(this.$table, this.table_options, this.$table_search);

            // cid
            this.cid = _.uniqueId('view');

            // Declare last_nid
            this.last_nid = null;

            // Declare current_item
            this.current_item = null;

            this.force_reload = false;
        }

        if (this._extra_init)
            this._extra_init();

        this.initialize();
        this.delegateEvents();
    };


    _.extend(TabView.prototype, {
        disabled_message: 'Access Denied',

        delegateEvents: function(events) {
            if (!(events || (events = _.result(this, 'events')))) return this;

            this.undelegateEvents();

            for (var key in events) {
                // var method = events[key];
                // if (!_.isFunction(method)) method = this[events[key]];
                var method = this[events[key]];

                if (!method) continue;

                var match = key.match(delegateEventSplitter);
                var eventName = match[1],
                    selector = match[2];

                method = _.bind(method, this);
                eventName += '.delegateEvents' + this.cid;
                if (selector === '') {
                    this.$el.on(eventName, method);
                } else {
                    this.$el.on(eventName, selector, method);
                }
            }
            return this;
        },

        undelegateEvents: function() {
            this.$el.off('.delegateEvents' + this.cid);
            return this;
        },

        checkAccess: function(params) {
            if (this.authenticate !== undefined) {
                return this.authenticate(params);
            } else {
                return $.when(true);
            }
        },

        renderTab: function(params) {
            /*
             * This method shouldn't be called manually
             */
            console.info('renderTab', params);

            // Two concerns: nid, rid
            var _this = this;

            this.checkAccess(params).then(function(json) {
                // Have access, go on rendering process
                console.info('Have access, go on rendering process');

                _this.enableTab();

                if (_this.$table) {
                    // Clear table
                    if (!params.nid) {
                        _this.clearTable();
                        _this.afterClearTable(params);
                        return;
                    }

                    var fetch_defer;

                    if (_this.last_nid != params.nid || _this.force_reload) {
                        // Need re-fetch

                        // Reset force_reload flag
                        _this.force_reload = false;

                        console.info('call fetchTableData', _this.force_reload);
                        fetch_defer = _this.fetchTableData(params.nid);

                        fetch_defer.then(function(json) {
                            _this.renderTable(json.data);
                            _this.afterRenderTable(params);

                            _this.last_nid = params.nid;  // NOTE Could be vulnerable if switch nid rapidly
                        });
                    }

                    $.when(fetch_defer).then(function() {
                        console.log('then params', params);
                        if (params.rid) {
                            // Get row dom
                            var row = _this.$table.find('[data-id=' + params.rid + ']');
                            console.log('row', row.length);
                            if (!row.length) {
                                loki.notify('No row id ' + params.rid, 'error');
                                return;
                            }

                            // Select row DataTable
                            _this.table_dt.selectRow(row[0]);
                            _this.current_item = _this.table_dt.getSelectedOne();

                            console.info('call onSelectRow');
                            _this.onSelectRow(_this.rid, _this.current_item);
                        } else {
                            _this.deselectTable();
                            console.info('call onDeselectRow');
                            _this.onDeselectRow();
                        }
                    });
                }

                // Call user's handleParams
                _this.handleParams(params);

            }, function(xhr) {
                // No access, disable this tab
                console.warn('No access, disable the tab');

                _this.disableTab();
            });
        },

        enableTab: function() {
            // Tab a
            $('a[alt=#' + this.$el.attr('id') + ']').parent().removeClass('disabled');

            // Cover
            var cover = this.$el.find('> .cover');
            if (!cover.length)
                return;
            cover.hide();
        },

        disableTab: function(message) {
            // Tab a
            $('a[alt=#' + this.$el.attr('id') + ']').parent().addClass('disabled');

            // Cover
            var cover = this.$el.find('> .cover');
            if (!message)
                message = this.disabled_message;

            if (!cover.length) {
                cover = $('<div></div>').addClass('cover');
                this.$el.append(cover);
            }
            cover.html(message);
            cover.show();
        },

        _createDataTable: function(el, extraOptions, searchInput) {
            var options = {
                // dom: 'T<"clear">ltir',
                // // dom: 'T<"clear">lfrtip',
                // paging: false,
                // scrollY: '400px',
                // scrollCollapse: true,
                // language: loki.datatables_config.language,
                // processing: false,
                tableTools: {
                    "aButtons": []
                },
            };

            if (this.table_selectable) {
                options.tableTools.sRowSelect = 'single';  // or 'multi'
            }

            $.extend(options, extraOptions);

            // Tweak rowCallback
            var cb;
            if ('rowCallback' in options) {
                var extra_cb = options.rowCallback;
                cb = function(row, data) {
                    $(row).attr('data-id', data.id);
                    extra_cb(row, data);
                };
            } else {
                cb = function(row, data) {
                    $(row).attr('data-id', data.id);
                };
            }
            options.rowCallback = cb;

            // Bind click event
            if (this.table_selectable) {
                el.on('click', 'tr', function() {
                    console.log('click tr');
                    var params = loki.getParams(),
                        obj = dt.getSelectedOne();

                    // `rid` means row id in table
                    if (obj) {
                        params.rid = obj.id;
                    } else {
                        if ('rid' in params)
                            delete params.rid;
                    }
                    loki.route(params);
                });
            }


            // Create DataTable instance
            var dt = datatables.createDataTable(el, options, searchInput);

            // var dt = el.DataTable(options);

            // if (searchInput) {
            //     searchInput.on('keyup change', function() {
            //         dt
            //             .column(0)
            //             .search(this.value)
            //             .draw();
            //     });
            // }

            return dt;
        },

        renderTable: function(data) {
            this.table_dt.reloadData(data);
        },

        clearTable: function() {
            console.info('call clearTable');
            this.table_dt.clear().draw();
        },

        deselectTable: function() {
            this.table_dt.tt().fnSelectNone();
        },

        notifySuccess: function(json) {
            console.log('ajax success', json);
            loki.notify('ajax success');
        },

        notifyError: function(jqXHR) {
            console.log('ajax error', jqXHR);
            var json = jqXHR.responseJSON;
            loki.notify(json.error.message, 'error');
        },

        /* User methods */

        initialize: function() {
        },

        handleParams: function(params) {
        },

        fetchTableData: function() {
        },

        afterRenderTable: function() {
            console.info('call afterRenderTable');
        },

        afterClearTable: function() {
            console.info('call afterClearTable');
        },

        onSelectRow: function() {
            console.warn('Please define onSelectRow for the inherited layout class');
        },

        onDeselectRow: function() {
            console.warn('Please define onDeselectRow for the inherited layout class');
        },

        // onSelectNode: function() {
        // },

        // onDeselectNode: function() {
        // },
    });

    TabView.extend = __class_extend;


    var registerTabViews = exports.registerTabViews = function() {
        /*
        tabs: {
            '1': 'User',
            '2': 'Admin',
        },
        ptree_tab_configs: {
            User: {
                mode: 'disable',
                levels: []
            },
            Admin: {
                mode: 'disable',
                levels: []
            },
        },
        */

        loki.tab_views = {};

        var tab_views = Array.prototype.slice.call(arguments),
            tabs_args = {},
            tabs_ptree_configs = {},
            tab_inits = {},
            tab_handlers = {},
            count = 1;

        tab_views.forEach(function(tv) {
            var tv_proto = tv.prototype,
                name = tv_proto.tab_name;

            tabs_args[count] = name;
            count += 1;

            if (tv_proto.ptree_config !== undefined)
                tabs_ptree_configs[name] = tv_proto.ptree_config;

            tab_inits['init' + name] = function(params) {
                loki.tab_views[name] = new tv();
            };

            tab_handlers['handle' + name] = function(params) {
                // loki.tab_views[name].handleParams(params);
                loki.tab_views[name].renderTab(params);
            };
        });

        console.log('[ tab-view ] registerTabViews', tabs_args, tabs_ptree_configs);

        // Configure tabs
        loki.configure({
            tabs: tabs_args,
            ptree_tab_configs: tabs_ptree_configs,
        });

        // Tab initializers
        loki.defineTabInitializers(tab_inits);

        // Tab Handlers
        loki.defineTabHandlers(tab_handlers);
    };

    return exports;
});
