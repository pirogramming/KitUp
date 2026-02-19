document.addEventListener('DOMContentLoaded', function() {
    if (!PROJECT_ID) return;
    
    // 체크 아이콘 클릭
    document.querySelectorAll('.check_icon').forEach(icon => {
        icon.addEventListener('click', function(e) {
            e.stopPropagation();
            
            const missionItem = this.closest('.mission_item');
            const cardId = missionItem.dataset.cardId;
            const isCompleted = missionItem.classList.contains('completed');
            
            // UI 업데이트
            if (isCompleted) {
                missionItem.classList.remove('completed');
                this.src = this.src.replace('check.png', 'nocheck.png');
            } else {
                missionItem.classList.add('completed');
                this.src = this.src.replace('nocheck.png', 'check.png');
            }
            
            // DB 저장 (API URL 사용)
            fetch(`/api/guides/card/${cardId}/toggle/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    project_id: PROJECT_ID,
                    is_completed: !isCompleted
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                }
            })
            .catch(error => console.error('Error:', error));
        });
    });
    
    // 카드 펼치기/접기
    document.querySelectorAll('.card_header').forEach(header => {
        header.addEventListener('click', function(e) {
            if (e.target.classList.contains('check_icon')) return;
            
            const card = this.closest('.mission_card');
            const missionItem = this.closest('.mission_item');
            
            // 다른 카드 닫기
            document.querySelectorAll('.mission_card').forEach(c => {
                c.classList.remove('active');
            });
            document.querySelectorAll('.mission_item').forEach(item => {
                item.classList.remove('active');
            });
            
            // 현재 카드 토글
            card.classList.toggle('active');
            missionItem.classList.toggle('active');
        });
    });
    
    // CSRF 토큰 가져오기
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});