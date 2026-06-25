/**
 * 影视影评分享系统 - 全局 JavaScript
 */

// jQuery AJAX 全局 CSRF Token 配置
$(function() {
    var csrfToken = $('meta[name="csrf-token"]').attr('content');
    if (csrfToken) {
        $.ajaxSetup({
            headers: { 'X-CSRFToken': csrfToken }
        });
    }

    // ========== 通知轮询 ==========
    var $notificationBadge = $('#notificationBadge');
    var $notificationMenu = $('#notificationMenu');

    function fetchNotifications() {
        if ($notificationBadge.length === 0) return; // 未登录时不请求
        $.get('/user/notifications', function(data) {
            if (!data.success) return;

            var unreadMessages = data.unread_messages || 0;
            var pendingRequests = data.pending_requests || 0;
            var total = data.total || 0;

            // 更新角标
            if (total > 0) {
                $notificationBadge
                    .text(total > 99 ? '99+' : total)
                    .removeClass('d-none');
            } else {
                $notificationBadge.addClass('d-none');
            }

            // 更新下拉菜单内容
            var menuHtml = '';
            if (total === 0) {
                menuHtml = '<li class="text-center py-3 text-muted">暂无新通知</li>';
            } else {
                if (unreadMessages > 0) {
                    menuHtml += '<li><a class="dropdown-item d-flex align-items-center" href="/user/friends">' +
                        '<i class="bi bi-chat-dots me-2 text-primary"></i>' +
                        '<span><strong>' + unreadMessages + '</strong> 条未读消息</span>' +
                        '</a></li>';
                }
                if (pendingRequests > 0) {
                    menuHtml += '<li><a class="dropdown-item d-flex align-items-center" href="/user/friends">' +
                        '<i class="bi bi-person-plus me-2 text-warning"></i>' +
                        '<span><strong>' + pendingRequests + '</strong> 个待处理好友请求</span>' +
                        '</a></li>';
                }
            }
            menuHtml += '<li><hr class="dropdown-divider"></li>' +
                '<li><a class="dropdown-item text-center text-primary" href="/user/friends">' +
                '<i class="bi bi-people"></i> 查看全部好友</a></li>';

            $notificationMenu.html(menuHtml);
        });
    }

    // 首次加载 + 每 10 秒轮询
    if ($notificationBadge.length) {
        fetchNotifications();
        setInterval(fetchNotifications, 10000);
    }
});

// 自动隐藏 Flash 消息（5秒后）
document.addEventListener('DOMContentLoaded', function () {
    var alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
});
