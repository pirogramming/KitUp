document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('reportModal');
    const openBtn = document.querySelector('.btn_report'); 
    const closeBtns = document.querySelectorAll('.close-btn');
    const form = document.getElementById("reportForm");
    const textarea = form.querySelector("textarea[name='reason']");


    /* CSRF */
    function getCookie(name) {
        const v = document.cookie.match("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)");
        return v ? v.pop() : "";
    }

    // 팝업 열기
    if(openBtn) {
        openBtn.addEventListener('click', function(e) {
            e.preventDefault();
            modal.style.display = 'flex'; 
        });
    }

    // 팝업 닫기
    closeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            modal.style.display = 'none';
            form.reset();
        });
    });

    // 배경 클릭 시 닫기
    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const selected = form.querySelector(
            "input[name='reported_user']:checked"
        );
        const reason = textarea.value.trim();

        if (!selected) {
            alert("신고할 팀원을 선택해주세요.");
            return;
        }
        if (!reason) {
            alert("신고 사유를 입력해주세요.");
            return;
        }

        try {
            const res = await fetch("/api/accounts/report/create", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCookie("csrftoken"),
                },
                credentials: "same-origin",
                body: JSON.stringify({
                    reported_user_id: selected.value,
                    reason: reason,
                }),
            });

            const data = await res.json();

            if (!res.ok) {
                alert(data.error || "신고에 실패했습니다.");
                return;
            }

            alert("신고가 접수되었습니다.");
            modal.style.display = "none";
            form.reset();
        } catch (err) {
            alert("네트워크 오류가 발생했습니다.");
        }
    });
});

document.addEventListener("DOMContentLoaded", function() {
    const links = document.querySelectorAll('.l_content a');
    links.forEach(link => {
        link.setAttribute('target', '_blank');
        link.setAttribute('rel', 'noopener noreferrer'); // 보안 강화
    });
});