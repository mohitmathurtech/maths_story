/**
 * Sound effects and confetti utilities for gamification.
 */
import confetti from "canvas-confetti";

// Lightweight sound effects using Web Audio API (no external files)
const audioCtx =
    typeof window !== "undefined"
        ? new (window.AudioContext || window.webkitAudioContext)()
        : null;

function playTone(frequency, duration, type = "sine", volume = 0.15) {
    if (!audioCtx) return;
    try {
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = type;
        osc.frequency.setValueAtTime(frequency, audioCtx.currentTime);
        gain.gain.setValueAtTime(volume, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + duration);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start();
        osc.stop(audioCtx.currentTime + duration);
    } catch (e) {
        // Silently fail — sound is not critical
    }
}

export function playCorrectSound() {
    playTone(523, 0.12, "sine", 0.12); // C5
    setTimeout(() => playTone(659, 0.12, "sine", 0.12), 80); // E5
    setTimeout(() => playTone(784, 0.18, "sine", 0.12), 160); // G5
}

export function playWrongSound() {
    playTone(330, 0.2, "square", 0.06); // E4 — softer buzz
    setTimeout(() => playTone(277, 0.25, "square", 0.06), 150); // C#4
}

export function playQuizCompleteSound() {
    const notes = [523, 659, 784, 1047]; // C E G C
    notes.forEach((f, i) =>
        setTimeout(() => playTone(f, 0.25, "sine", 0.1), i * 120)
    );
}

export function playStreakSound() {
    playTone(880, 0.1, "sine", 0.1);
    setTimeout(() => playTone(1047, 0.15, "sine", 0.1), 100);
    setTimeout(() => playTone(1319, 0.2, "sine", 0.1), 200);
}

// Confetti effects
export function fireConfetti() {
    confetti({
        particleCount: 120,
        spread: 80,
        origin: { y: 0.6 },
        colors: ["#6366f1", "#f59e0b", "#10b981", "#ec4899", "#3b82f6"],
    });
}

export function fireConfettiCannon() {
    // Left cannon
    confetti({
        particleCount: 60,
        angle: 60,
        spread: 55,
        origin: { x: 0, y: 0.7 },
        colors: ["#6366f1", "#f59e0b", "#10b981"],
    });
    // Right cannon
    confetti({
        particleCount: 60,
        angle: 120,
        spread: 55,
        origin: { x: 1, y: 0.7 },
        colors: ["#ec4899", "#3b82f6", "#8b5cf6"],
    });
}

export function firePerfectScoreConfetti() {
    const duration = 2000;
    const end = Date.now() + duration;

    (function frame() {
        confetti({
            particleCount: 4,
            angle: 60,
            spread: 55,
            origin: { x: 0 },
            colors: ["#6366f1", "#f59e0b", "#10b981"],
        });
        confetti({
            particleCount: 4,
            angle: 120,
            spread: 55,
            origin: { x: 1 },
            colors: ["#ec4899", "#3b82f6", "#8b5cf6"],
        });
        if (Date.now() < end) requestAnimationFrame(frame);
    })();
}
