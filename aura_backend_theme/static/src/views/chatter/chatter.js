/** @odoo-module **/

const STORAGE_WIDTH_KEY = "tbt.chatter.width";
const STORAGE_COLLAPSED_KEY = "tbt.chatter.collapsed";
const MIN_WIDTH = 300;
const MAX_WIDTH = 680;
const DESKTOP_MIN_WIDTH = 1200;

function clampWidth(value) {
    return Math.min(MAX_WIDTH, Math.max(MIN_WIDTH, value));
}

function applyWidth(container, width) {
    const next = clampWidth(width);
    container.style.width = `${next}px`;
    container.style.flex = `0 0 ${next}px`;
}

function ensureControls(container) {
    if (container.dataset.tbtChatterInit === "1") {
        return;
    }
    container.dataset.tbtChatterInit = "1";
    container.classList.add("tbt_chatter_container");

    const handle = document.createElement("div");
    handle.className = "tbt_chatter_resize_handle";
    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "tbt_chatter_toggle";

    handle.addEventListener("mousedown", (ev) => {
        if (window.innerWidth < DESKTOP_MIN_WIDTH) {
            return;
        }
        if (container.classList.contains("tbt_chatter_collapsed")) {
            return;
        }
        ev.preventDefault();

        const startX = ev.clientX;
        const startWidth = container.getBoundingClientRect().width;

        const onMouseMove = (moveEv) => {
            const delta = startX - moveEv.clientX;
            applyWidth(container, startWidth + delta);
            localStorage.setItem(STORAGE_WIDTH_KEY, String(clampWidth(startWidth + delta)));
        };

        const onMouseUp = () => {
            document.removeEventListener("mousemove", onMouseMove);
            document.removeEventListener("mouseup", onMouseUp);
        };

        document.addEventListener("mousemove", onMouseMove);
        document.addEventListener("mouseup", onMouseUp);
    });

    const setCollapsed = (collapsed) => {
        if (window.innerWidth < DESKTOP_MIN_WIDTH) {
            collapsed = false;
        }
        container.classList.toggle("tbt_chatter_collapsed", collapsed);
        toggle.setAttribute("aria-expanded", collapsed ? "false" : "true");
        toggle.setAttribute("title", collapsed ? "Expand chatter" : "Collapse chatter");
        toggle.innerHTML = collapsed ? "&#x2039;" : "&#x203A;";
        localStorage.setItem(STORAGE_COLLAPSED_KEY, collapsed ? "1" : "0");
    };

    toggle.addEventListener("click", () => {
        setCollapsed(!container.classList.contains("tbt_chatter_collapsed"));
    });

    container.append(handle);
    container.append(toggle);

    const savedWidth = Number.parseInt(localStorage.getItem(STORAGE_WIDTH_KEY) || "", 10);
    if (Number.isFinite(savedWidth)) {
        applyWidth(container, savedWidth);
    }
    const savedCollapsed = localStorage.getItem(STORAGE_COLLAPSED_KEY) === "1";
    setCollapsed(savedCollapsed);

    const syncDesktopMode = () => {
        const isDesktop = window.innerWidth >= DESKTOP_MIN_WIDTH;
        container.classList.toggle("tbt_chatter_desktop", isDesktop);
        if (!isDesktop) {
            container.classList.remove("tbt_chatter_collapsed");
            container.style.width = "";
            container.style.flex = "";
            toggle.setAttribute("aria-expanded", "true");
            toggle.setAttribute("title", "Collapse chatter");
            toggle.innerHTML = "&#x203A;";
        }
    };
    syncDesktopMode();
    window.addEventListener("resize", syncDesktopMode);
}

function initializeAll() {
    document.querySelectorAll(".o-mail-ChatterContainer.o-mail-Form-chatter").forEach((container) => {
        if (!container.classList.contains("o-aside")) {
            return;
        }
        ensureControls(container);
    });
}

const observer = new MutationObserver(initializeAll);

let observerStarted = false;

function startObserver() {
    if (observerStarted) return;
    const target = document.body || document.documentElement;
    if (!target) return;
    observerStarted = true;
    initializeAll();
    observer.observe(target, { childList: true, subtree: true });
}

startObserver();
if (!observerStarted) {
    window.addEventListener("DOMContentLoaded", startObserver, { once: true });
}
