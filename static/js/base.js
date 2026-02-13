document.addEventListener('DOMContentLoaded', function() {
    const hamburger = document.querySelector('.hamburger');
    const headerMenu = document.querySelector('.header_menu');
    const mobileOverlay = document.querySelector('.mobile-overlay');
    const dropdowns = document.querySelectorAll('.dropdown');
    
    // 메뉴 닫기 함수
    function closeMenu() {
        if (hamburger) hamburger.classList.remove('active');
        if (headerMenu) headerMenu.classList.remove('active');
        if (mobileOverlay) mobileOverlay.classList.remove('active');
        document.body.style.overflow = '';
        
        // 모든 드롭다운 닫기
        dropdowns.forEach(dropdown => {
            dropdown.classList.remove('active');
        });
    }
    
    // 햄버거 메뉴 토글
    if (hamburger) {
        hamburger.addEventListener('click', function(e) {
            e.stopPropagation();
            const isActive = this.classList.contains('active');
            
            if (isActive) {
                closeMenu();
            } else {
                this.classList.add('active');
                headerMenu.classList.add('active');
                mobileOverlay.classList.add('active');
                document.body.style.overflow = 'hidden';
            }
        });
    }
    
    // 오버레이 클릭시 메뉴 닫기
    if (mobileOverlay) {
        mobileOverlay.addEventListener('click', function(e) {
            e.stopPropagation();
            closeMenu();
        });
    }
    
    // 메뉴 내부 클릭은 전파 막기
    if (headerMenu) {
        headerMenu.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    }
    
    // 모바일에서 드롭다운 클릭 처리
    dropdowns.forEach(dropdown => {
        const dropdownLink = dropdown.querySelector('a');
        
        if (dropdownLink) {
            dropdownLink.addEventListener('click', function(e) {
                // 768px 이하에서만 드롭다운 토글
                if (window.innerWidth <= 768) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    const isCurrentlyActive = dropdown.classList.contains('active');
                    
                    // 모든 드롭다운 닫기
                    dropdowns.forEach(d => {
                        d.classList.remove('active');
                    });
                    
                    // 현재 드롭다운이 닫혀있었으면 열기
                    if (!isCurrentlyActive) {
                        dropdown.classList.add('active');
                    }
                }
            });
        }
    });
    
    // 드롭다운 내부 링크 클릭시 메뉴 닫기
    const dropdownLinks = document.querySelectorAll('.dropdown-content a');
    dropdownLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            if (window.innerWidth <= 768) {
                // 링크 클릭시 메뉴 닫기
                setTimeout(() => {
                    closeMenu();
                }, 100);
            }
        });
    });
    
    // 메뉴 외부 클릭시 닫기
    document.addEventListener('click', function(e) {
        if (window.innerWidth <= 768) {
            if (!headerMenu.contains(e.target) && !hamburger.contains(e.target)) {
                closeMenu();
            }
        }
    });
    
    // 창 크기 변경시 메뉴 상태 초기화
    window.addEventListener('resize', function() {
        if (window.innerWidth > 768) {
            closeMenu();
        }
    });
});