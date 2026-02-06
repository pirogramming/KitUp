// mission.js - 수정된 버전

document.addEventListener('DOMContentLoaded', function() {
    const missionCards = document.querySelectorAll('.mission_card');
    
    missionCards.forEach(card => {
        card.addEventListener('click', function() {
            const isActive = this.classList.contains('active');
            const missionItem = this.closest('.mission_item');
            
            // 다른 모든 카드와 mission_item에서 active 제거
            document.querySelectorAll('.mission_card').forEach(c => {
                c.classList.remove('active');
            });
            document.querySelectorAll('.mission_item').forEach(item => {
                item.classList.remove('active');
            });
            
            // 클릭한 카드와 mission_item에 active 추가
            if (!isActive) {
                this.classList.add('active');
                missionItem.classList.add('active');
            }
        });
        
        // 체크 아이콘 클릭 시 완료 처리
        const checkIcon = card.querySelector('.check_icon');
        checkIcon.addEventListener('click', function(e) {
            e.stopPropagation();
            
            const card = this.closest('.mission_card');
            const missionItem = card.closest('.mission_item');
            const isCompleted = card.classList.contains('completed');
            
            if (isCompleted) {
                card.classList.remove('completed');
                missionItem.classList.remove('completed');
                this.src = this.src.replace('check.png', 'nocheck.png');
            } else {
                card.classList.add('completed');
                missionItem.classList.add('completed');
                this.src = this.src.replace('nocheck.png', 'check.png');
            }
        });
    });
});