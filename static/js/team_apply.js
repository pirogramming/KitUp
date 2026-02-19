const showToast = (message, type = "success") => {
    const toast = document.createElement("div");
    toast.className = `ref-toast ref-toast-${type}`;
    toast.textContent = message;

    Object.assign(toast.style, {
        position: "fixed",
        bottom: "50px",
        left: "50%",
        transform: "translateX(-50%) translateY(20px)",
        background: type === "success" ? "#4272EF" : "#FF6B6B",
        color: "#fff",
        padding: "12px 25px",
        borderRadius: "30px",
        fontSize: "15px",
        fontWeight: "500",
        boxShadow: "0 4px 15px rgba(0,0,0,0.2)",
        opacity: "0",
        transition: "all 0.3s ease",
        zIndex: "9999",
    });

    document.body.appendChild(toast);

    requestAnimationFrame(() => {
        toast.style.opacity = "1";
        toast.style.transform = "translateX(-50%) translateY(0)";
    });

    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateX(-50%) translateY(20px)";
        setTimeout(() => toast.remove(), 300);
    }, 2000);
};

const bindNotifyBtn = () => {
    document.querySelectorAll(".noti_button").forEach(btn => {
        btn.addEventListener("click", (e) => {
            e.preventDefault();

            const form = btn.closest("form");

            fetch(form.action, {
                method: "POST",
                body: new FormData(form),
            })
            .then(res => {
                if (res.ok) {
                    showToast("알림 신청이 완료되었습니다.", "success");
                    btn.disabled = true;
                    btn.textContent = "신청 완료";
                    btn.style.background = "#ccc";
                } else {
                    showToast("신청 중 오류가 발생했습니다.", "error");
                }
            })
            .catch(() => showToast("네트워크 오류가 발생했습니다.", "error"));
        });
    });
};

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bindNotifyBtn);
} else {
    bindNotifyBtn();
}