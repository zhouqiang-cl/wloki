define([
    'datatables',
    'datatables-tabletools',
], function(DataTables, TableTools) {
    // console.log('===DataTables===', DataTables, TableTools);
    var exports = {};

    var _language = {
            "sProcessing":   "处理中...",
            "sLengthMenu":   "显示 _MENU_ 项结果",
            "sZeroRecords":  "没有匹配结果",
            "sInfo":         "显示第 _START_ 至 _END_ 项结果，共 _TOTAL_ 项",
            "sInfoEmpty":    "显示第 0 至 0 项结果，共 0 项",
            "sInfoFiltered": "(由 _MAX_ 项结果过滤)",
            "sInfoPostFix":  "",
            "sSearch":       "搜索:",
            "sUrl":          "",
            "sEmptyTable":     "表中数据为空",
            "sLoadingRecords": "载入中...",
            "sInfoThousands":  ",",
            "oPaginate": {
                "sFirst":    "首页",
                "sPrevious": "上页",
                "sNext":     "下页",
                "sLast":     "末页"
            },
            "oAria": {
                "sSortAscending":  ": 以升序排列此列",
                "sSortDescending": ": 以降序排列此列"
            }
        },

        default_options = {
            dom: 'T<"clear">ltir',
            // dom: 'T<"clear">lfrtip',
            paging: false,
            // scrollY: '400px',
            scrollCollapse: true,
            tableTools: {
                // "sRowSelect": "single",  // or 'multi'
                "aButtons": []
            },
            language: _language,
            processing: true,
        };


    var createDataTable = exports.createDataTable = function(el, extraOptions, searchInput) {
        var options = {};
        $.extend(true, options, default_options);
        $.extend(true, options, extraOptions);
        console.log('[ datatables ] createDataTable options:', options);

        var dt = el.DataTable(options);

        if (searchInput) {
            searchInput.on('keyup change', function() {
                dt
                    .column(0)
                    .search(this.value)
                    .draw();
            });
        }

        return dt;
    };


    var extra_apis = {
        tt: function() {
            /* Return TableTools instance */
            return TableTools.fnGetInstance(this.table().node());
        },

        selectRow: function(row) {
            return this.tt().fnSelect(row);
        },

        $find: function(query) {
            return $(this.table().node()).find(query);
        },

        displayProcessing: function(processing) {
            var container = $(this.table().container()),
                processingTip = container.find('.dataTables_processing');
            if (processing === undefined)
                processing = true;

            if (processing) {
                processingTip.show();
                // container.css('pointer-events', 'none');
                container.addClass('-disabled');
            } else {
                // container.css('pointer-events', 'auto');
                container.removeClass('-disabled');
                processingTip.hide();
            }
        },

        reloadData: function(data) {
            if (this.data().length)
                this.clear();
            this.rows.add(data).draw();
        },

        clearData: function(data) {
            this.clear();
            this.draw();
        },

        adjustWidth: function() {
            this.columns.adjust().draw();
        },

        getSelectedOne: function(data) {
            var selected = this.rows('.selected').data();
            if (selected.length)
                return selected[0];
            else
                return null;
        },
    };

    // Register extra APIs
    for (var _name in extra_apis) {
        $.fn.dataTable.Api.register(_name, extra_apis[_name]);
    }

    return exports;
});
