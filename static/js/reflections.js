// static/js/reflections.js
(() => {
  /** ---------------------------
   *  Helpers
   * -------------------------- */
  const qs = (sel, el = document) => el.querySelector(sel);
  const qsa = (sel, el = document) => Array.from(el.querySelectorAll(sel));

  const closeAllMenus = (exceptWrap = null) => {
    qsa("[data-more-wrap]").forEach((wrap) => {
      if (exceptWrap && wrap === exceptWrap) return;
      const btn = qs("[data-more-btn]", wrap);
      const menu = qs("[data-more-menu]", wrap);
      if (!btn || !menu) return;
      btn.setAttribute("aria-expanded", "false");
      menu.hidden = true;
    });
  };

  const showToast = (message, type = "success") => {
    const toast = document.createElement("div");
    toast.className = `ref-toast ref-toast-${type}`;
    toast.textContent = message;

    document.body.appendChild(toast);

    requestAnimationFrame(() => {
      toast.classList.add("show");
    });

    setTimeout(() => {
      toast.classList.remove("show");
      setTimeout(() => toast.remove(), 300);
    }, 2000);
  };

  /** ---------------------------
   *  1) Kebab menu (수정/삭제)
   *     - 버튼 클릭: 해당 메뉴 토글
   *     - 바깥 클릭: 모두 닫기
   *     - ESC: 닫기
   * -------------------------- */
  const bindMenus = () => {
    qsa("[data-more-wrap]").forEach((wrap) => {
      const btn = qs("[data-more-btn]", wrap);
      const menu = qs("[data-more-menu]", wrap);
      if (!btn || !menu) return;

      btn.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();

        const isOpen = btn.getAttribute("aria-expanded") === "true";
        closeAllMenus(wrap);

        // 토글
        btn.setAttribute("aria-expanded", String(!isOpen));
        menu.hidden = isOpen;

        // 열릴 때만 포커스 이동(접근성)
        if (!isOpen) {
          const firstItem = qs(".note-menuitem", menu);
          if (firstItem) firstItem.focus?.();
        }
      });

      // 메뉴 내부 클릭은 바깥 클릭 닫기 막기
      menu.addEventListener("click", (e) => e.stopPropagation());
    });

    // 바깥 클릭하면 닫기
    document.addEventListener("click", () => closeAllMenus(null));

    // ESC 누르면 닫기
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") closeAllMenus(null);
    });
  };

  /** ---------------------------
   *  2) Bookmark toggle (AJAX 포함)
   *     - 기본값 false로 시작 (서버값 무시)
   *     - 클릭 시 UI만 토글
   *     - aria-pressed, class 동기화
   * -------------------------- */
  const getCSRFToken = () =>
  (document.querySelector("[name=csrfmiddlewaretoken]") || {}).value ||
  (document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/) || [])[1] ||
  "";

  const bindBookmarkAjax = () => {
    document.querySelectorAll("[data-bookmark-btn]").forEach((btn) => {
      btn.addEventListener("click", async (e) => {
        console.log("bookmark btn clicked");
        e.preventDefault();
        e.stopPropagation();

        // note id 추출 (A안/B안 모두 대응)
        const noteId =
          btn.dataset.noteId ||
          btn.closest("[data-note-id]")?.dataset.noteId;

        if (!noteId) {
          console.error("noteId not found for bookmark button");
          return;
        }

        // 현재 상태
        const wasActive = btn.classList.contains("is-active");
        const next = !wasActive;

        // 옵티미스틱 UI
        btn.classList.toggle("is-active", next);
        btn.setAttribute("aria-pressed", next ? "true" : "false");
        btn.disabled = true;

        try {
          const res = await fetch(`/api/reflections/retrospectives/${noteId}/`, {
            method: "PATCH",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": getCSRFToken(),
            },
            body: JSON.stringify({ bookmarked: next }),
          });

          if (!res.ok) {
            const t = await res.text().catch(() => "");
            throw new Error(`PATCH failed: ${res.status} ${t}`);
          }

          // 응답이 bookmarked를 내려주면 동기화(선택)
          const data = await res.json().catch(() => null);
          if (data?.bookmarked !== undefined) {
            btn.classList.toggle("is-active", !!data.bookmarked);
            btn.setAttribute("aria-pressed", data.bookmarked ? "true" : "false");
          }

        } catch (err) {
          console.error(err);

          // 실패 시 롤백
          btn.classList.toggle("is-active", wasActive);
          btn.setAttribute("aria-pressed", wasActive ? "true" : "false");

          alert("북마크 변경 실패");
        } finally {
          btn.disabled = false;
        }
      });
    });
  };

  

  const bindProjectRoleAutofill = () => {
    const projectSel = document.querySelector("[data-project-select]");
    const roleSel = document.querySelector("[data-role-select]");
    const roleMapEl = document.getElementById("roleMapJson");

    if (!projectSel || !roleSel || !roleMapEl) return;

    let roleMap = {};
    try {
      roleMap = JSON.parse(roleMapEl.textContent || "{}");
    } catch {
      roleMap = {};
    }

    const setRole = (val) => {
      roleSel.value = val || ""; // 개인 회고면 빈값
    };

    // 초기 상태(수정 페이지 대응): 프로젝트가 없으면 role 비우기
    if (!projectSel.value) setRole("");

    projectSel.addEventListener("change", () => {
      const pid = projectSel.value;

      // ✅ "선택 안 함(개인용)"이면 개인 회고로 리셋
      if (!pid) {
        setRole("");
        return;
      }

      // ✅ 프로젝트 선택하면 roleMap 기반으로 자동 세팅
      const autoRole = roleMap[pid];
      setRole(autoRole || "");
    });
  };


  const bindAssetUpload = () => {
    const fileInput = document.getElementById("assetFileInput");
    if (!fileInput) return;

    const wrap = document.querySelector(".ref-form-wrap");
    if (!wrap) return;

    const NOTE_ID = (wrap.dataset.noteId || "").trim();
    const DRAFT_KEY = (wrap.dataset.draftKey || "").trim();
    let currentQid = null;

    const csrfToken = (document.querySelector("[name=csrfmiddlewaretoken]") || {}).value || "";

    // ✅ URL name은 프로젝트에 맞춰야 함 (기존 _note_form.html에 있던 이름 그대로)
    const uploadUrlWithNote = NOTE_ID ? wrap.dataset.uploadNoteUrl : "";
    const uploadUrlTemp = wrap.dataset.uploadTempUrl;

    // 위 2개를 템플릿에서 data로 주는 방식이 제일 안전함.
    // (아래 "data-upload-..." 주는 방법 참고)

    const insertAtCursor = (textarea, text) => {
      const start = textarea.selectionStart ?? textarea.value.length;
      const end = textarea.selectionEnd ?? textarea.value.length;
      const before = textarea.value.slice(0, start);
      const after = textarea.value.slice(end);
      textarea.value = before + text + after;
      const pos = start + text.length;
      textarea.setSelectionRange(pos, pos);
      textarea.focus();
    };

    document.querySelectorAll("[data-asset-btn]").forEach((btn) => {
      btn.addEventListener("click", () => {
        currentQid = btn.dataset.qid;
        fileInput.value = "";
        fileInput.click();
      });
    });

    fileInput.addEventListener("change", async () => {
      if (!fileInput.files || !fileInput.files[0] || !currentQid) return;

      if (!NOTE_ID && !DRAFT_KEY) {
        alert("draft_key가 없어 업로드할 수 없습니다.");
        return;
      }

      const url = NOTE_ID ? uploadUrlWithNote : uploadUrlTemp;
      if (!url) {
        alert("업로드 URL이 설정되지 않았습니다.");
        return;
      }

      const fd = new FormData();
      fd.append("image", fileInput.files[0]);
      fd.append("alt_text", "image");
      if (!NOTE_ID) fd.append("draft_key", DRAFT_KEY);

      let res;
      try {
        res = await fetch(url, {
          method: "POST",
          headers: { "X-CSRFToken": csrfToken },
          body: fd,
        });
      } catch (e) {
        console.error(e);
        alert("업로드 요청 실패(네트워크)");
        return;
      }

      if (!res.ok) {
        const t = await res.text().catch(() => "");
        console.error("upload failed:", res.status, t);
        alert("업로드 실패");
        return;
      }

      const data = await res.json();
      const md = data.md || `![image](${data.url})`;

      const ta = document.getElementById(`ta__${currentQid}`);
      if (!ta) return;

      insertAtCursor(ta, (ta.value.endsWith("\n") || ta.value.length === 0) ? md : "\n" + md);
    });
  };

  const bindAssetDelete = () => {
    const wrap = document.querySelector(".ref-form-wrap");
    if (!wrap) return;

    const NOTE_ID = (wrap.dataset.noteId || "").trim();
    if (!NOTE_ID) return;

    const csrfToken = (document.querySelector("[name=csrfmiddlewaretoken]") || {}).value || "";

    document.querySelectorAll("[data-asset-delete]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        if (!confirm("이미지를 삭제할까요?")) return;

        const assetId = btn.dataset.assetId;
        const urlTpl = wrap.dataset.deleteAssetUrlTpl; // 예: "/retrospectives/12/assets/0/" 형태
        if (!urlTpl) return;

        const url = urlTpl.replace("/0/", `/${assetId}/`);

        const res = await fetch(url, {
          method: "DELETE",
          headers: { "X-CSRFToken": csrfToken },
        });

        if (!res.ok) {
          alert("삭제 실패");
          return;
        }

        const row = document.querySelector(`[data-asset-row="${assetId}"]`);
        if (row) row.remove();
      });
    });
  };
  const bindAutoSubmit = () => {
    document.querySelectorAll("[data-auto-submit]").forEach((el) => {
      el.addEventListener("change", () => {
        el.form?.submit();
      });
    });
  };

  const insertTableAtCursor = (textarea, rows = 2, cols = 2) => {
    console.log("insertTableAtCursor", { rows, cols });
    const headerCells = Array.from({ length: cols }, (_, i) => `헤더${i + 1}`);
    const dividerCells = Array.from({ length: cols }, () => "---");
    const bodyRows = Array.from({ length: rows }, () =>
      Array.from({ length: cols }, () => "내용")
    );

    const lines = [
      `| ${headerCells.join(" | ")} |`,
      `| ${dividerCells.join(" | ")} |`,
      ...bodyRows.map((row) => `| ${row.join(" | ")} |`),
      "", // 마지막 줄바꿈
    ];

    const table = `\n${lines.join("\n")}`;

    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const value = textarea.value;

    textarea.value = value.slice(0, start) + table + value.slice(end);

    const newPos = start + table.length;
    textarea.selectionStart = textarea.selectionEnd = newPos;
    textarea.focus();
  };

  const bindInsertTable = () => {
    const backdrop = document.querySelector(".ref-table-picker-backdrop");
    if (!backdrop) return;

    const sizeText = backdrop.querySelector(".ref-table-picker-size");
    const cancelBtn = backdrop.querySelector(".ref-table-picker-cancel");
    const cells = Array.from(backdrop.querySelectorAll(".ref-table-cell"));

    if (!sizeText || !cancelBtn || cells.length === 0) return;

    let targetTextarea = null;
    let hoverRows = 0, hoverCols = 0;

    const reset = () => {
      hoverRows = 0; hoverCols = 0;
      sizeText.textContent = "0 × 0";
      cells.forEach(c => c.classList.remove("active"));
    };

    const close = () => {
      backdrop.hidden = true;
      reset();
      targetTextarea = null;
    };

    // 표 버튼 클릭 -> 모달 오픈
    document.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-table-btn]");
      if (!btn) return;

      const qid = btn.dataset.qid;
      const ta = document.getElementById(`ta__${qid}`);
      if (!ta) return;

      targetTextarea = ta;
      reset();
      backdrop.hidden = false;
    });

    // hover -> 미리보기(하이라이트)
    cells.forEach((cell) => {
      cell.addEventListener("mouseenter", () => {
        hoverRows = +cell.dataset.rows;
        hoverCols = +cell.dataset.cols;

        cells.forEach((c) => {
          c.classList.toggle(
            "active",
            +c.dataset.rows <= hoverRows && +c.dataset.cols <= hoverCols
          );
        });

        sizeText.textContent = `${hoverRows} × ${hoverCols}`;
      });

      // ✅ click -> 즉시 삽입
      cell.addEventListener("click", () => {
        const r = +cell.dataset.rows;
        const c = +cell.dataset.cols;
        if (!targetTextarea || !r || !c) return;

        insertTableAtCursor(targetTextarea, r, c);
        close();
      });
    });

    // 취소/바깥/ESC 닫기
    cancelBtn.addEventListener("click", close);

    backdrop.addEventListener("click", (e) => {
      if (e.target === backdrop) close();
    });

    document.addEventListener("keydown", (e) => {
      if (!backdrop.hidden && e.key === "Escape") close();
    });
  };
  

  const bindBookmarkFilter = () => {
    const btn = document.querySelector("[data-bookmark-filter]");
    if (!btn) return;

    btn.addEventListener("click", () => {
      const url = new URL(window.location.href);
      const isOn = url.searchParams.get("bookmarked");

      if (isOn) {
        url.searchParams.delete("bookmarked");
      } else {
        url.searchParams.set("bookmarked", "1");
      }

      window.location.href = url.toString();
    });
  };

  const bindMDCopyBtn = () => {
    document.querySelectorAll("[data-md-copy]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const ta = document.getElementById(btn.dataset.targetId);
        if (!ta) return;

        try {
          await navigator.clipboard.writeText(ta.value);
          showToast("마크다운 복사 완료", "success");
        } catch (e) {
          console.error(e);
          showToast("마크다운 복사 실패", "error");
        }
      });
    });
  };
  
  const bindAutoResizeTextarea = () => {
    const resize = (ta) => {
      ta.style.height = "auto";
      ta.style.height = ta.scrollHeight + "px";
    };

    document.querySelectorAll(".ref-textarea").forEach((ta) => {
      // 초기 값 반영 (수정 페이지 대응)
      resize(ta);

      ta.addEventListener("input", () => resize(ta));
    });
  };



  /** ---------------------------
   *  Init
   * -------------------------- */
  const init = () => {
    bindMenus();
    bindBookmarkAjax();
    bindProjectRoleAutofill();
    bindAssetUpload();
    bindAssetDelete();
    bindAutoSubmit();
    bindBookmarkFilter();
    bindInsertTable();
    bindMDCopyBtn();
    bindAutoResizeTextarea();
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
