//Flot Line Chart
$(document).ready(function () {
    online_query_num_cal_func();
    sql_online_cal_by_db_func();
    order_status_cal_func();
});

asyncTag = false;

//在线查询次数统计
function online_query_num_cal_func() {
    $.ajax({
        url: '/api/online_query_cal',
        type: 'POST',
        async: asyncTag,
        error: function (resp) {
            console.log(resp);
        },
        success: function (resp) {
            data = $.parseJSON(resp);
            var options = {
                chart: {
                    type: 'line'
                },
                title: {
                    text: ''
                },
                xAxis: {
                    title: {
                        text: '日期'
                    },
                    categories: data.categories
                },
                yAxis: {
                    title: {
                        text: '查询次数'
                    }
                },
                series: data.series,
                credits: {
                    enabled: false //不显示LOGO
                },
            };
            // 图表初始化函数
            var chart = Highcharts.chart('online_query_num_line', options);
        }
    });
};

function sql_online_cal_by_db_func() {
    $.ajax({
        url: '/api/sql_online_cal_by_db',
        type: 'POST',
        async: asyncTag,
        error: function (resp) {
            console.log(resp);
        },
        success: function (resp) {
            data = $.parseJSON(resp);
            var plotObj = $.plot($("#flot-pie-chart"), data.data, {
                series: {
                    pie: {
                        show: true
                    }
                },
                grid: {
                    hoverable: true
                },
                tooltip: true,

                tooltipOpts: {
                    content: "%p.0%, %s", // show percentages, rounding to 2 decimal places
                    shifts: {
                        x: 20,
                        y: 0
                    },
                    defaultTheme: false
                }
            });
            $("#online_num_label").text('上线比例（上线总数：' + data.total.toString() + '）');
        }
    });
};

function order_status_cal_func(){
    $.ajax({
        url: '/api/order_status_cal',
        type: 'POST',
        async: asyncTag,
        error: function (resp) {
            console.log(resp);
        },
        success: function (resp) {
            data = $.parseJSON(resp);
            var plotObj = $.plot($("#order_status_cal"), data.data, {
                series: {
                    pie: {
                        show: true
                    }
                },
                grid: {
                    hoverable: true
                },
                tooltip: true,

                tooltipOpts: {
                    content: "%p.0%, %s", // show percentages, rounding to 2 decimal places
                    shifts: {
                        x: 20,
                        y: 0
                    },
                    defaultTheme: false
                }
            });
            $("#order_status_cal_label").text('工单状态（总数：' + data.total.toString() +'）');
        }
    });
};