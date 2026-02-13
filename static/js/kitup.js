// static/js/kitup.js

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

// 하트 버튼 클릭 핸들러
document.addEventListener("click", async (e) => {
  const btn = e.target.closest(".kitup-like-btn");
  if (!btn) return;

  // 이벤트 전파 방지
  e.preventDefault();
  e.stopPropagation();
  e.stopImmediatePropagation();

  const projectId = btn.dataset.projectId;
  
  console.log('좋아요 클릭:', projectId);
  
  try {
    // 좋아요 API 호출
    const response = await fetch(`/projects/all/${projectId}/like/`, {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCookie('csrftoken'),
      },
    });

    console.log('API 응답:', response.status);

    if (!response.ok) {
      throw new Error(`API 오류: ${response.status}`);
    }

    const data = await response.json();
    console.log('응답 데이터:', data);

    // UI 업데이트
    btn.dataset.liked = String(data.is_liked);
    btn.setAttribute("aria-pressed", String(data.is_liked));
    
    // 좋아요 수 업데이트
    let countEl = btn.nextElementSibling;
    if (countEl && countEl.classList.contains('kitup-like-count')) {
      countEl.textContent = data.like_count;
      console.log('좋아요 수 업데이트:', data.like_count);
    }
  } catch (error) {
    console.error('좋아요 처리 중 오류:', error);
    alert('좋아요 처리 중 오류가 발생했습니다: ' + error.message);
  }
}, true); // 캡처 단계에서 처리

