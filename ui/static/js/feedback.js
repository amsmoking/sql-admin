layui.use(['util', 'laydate', 'layer'], function () {
    var util = layui.util;
    //var laydate = layui.laydate; 
    var layer = layui.layer;
    //固定块
    util.fixbar({
        bar1: true,
        //bar2: true,
        css: { right: 50, bottom: 100 },
        bgcolor: '#393D49',
        click: function (type) {
            if (type === 'bar1') {
                layer.prompt({title: '反馈建议', formType: 2, value : '在这里拍砖。。。'}, function(text, index){
                    layer.close(index);
                    $.ajax({
                        url: '/feedback/add?text=' + text,
                        type: 'POST',
                        async: true,
                        error: function (resp) {
                            console.log(resp);
                        },
                        success: function (resp) {
                            console.log(resp);
                        }
                    });
                });
            }
        },
    });
});

/*
function (order_id, req_user) {
    $("#cancel_modal_label").text("ID:" + order_id);
    $("#cancel_modal").modal('show');
    $("#cancel_order_id").val(order_id);
};*/