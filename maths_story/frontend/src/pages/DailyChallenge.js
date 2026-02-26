import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import {
    Brain,
    ArrowLeft,
    Calendar,
    CheckCircle,
    XCircle,
    Trophy,
    Clock,
    Send,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import api from "@/utils/api";
import DarkModeToggle from "@/components/DarkModeToggle";
import { playCorrectSound, playWrongSound, fireConfetti } from "@/utils/sounds";

export default function DailyChallenge({ user, onLogout }) {
    const navigate = useNavigate();
    const [challenge, setChallenge] = useState(null);
    const [completed, setCompleted] = useState(false);
    const [submittedResult, setSubmittedResult] = useState(null);
    const [answers, setAnswers] = useState({});
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);

    useEffect(() => {
        fetchChallenge();
    }, []);

    const fetchChallenge = async () => {
        try {
            const res = await api.get("/daily/challenge");
            setChallenge(res.data.challenge);
            setCompleted(res.data.completed);
            setSubmittedResult(res.data.result);
        } catch (err) {
            toast.error("Failed to load daily challenge");
        } finally {
            setLoading(false);
        }
    };

    const handleAnswer = (qId, answer) => {
        setAnswers({ ...answers, [qId]: answer });
    };

    const handleSubmit = async () => {
        const questions = challenge?.questions || [];
        if (Object.keys(answers).length < questions.length) {
            toast.error("Please answer all questions before submitting");
            return;
        }

        setSubmitting(true);
        try {
            const payload = {
                answers: questions.map((q) => ({
                    question_id: q.id,
                    user_answer: answers[q.id] || "",
                })),
            };
            const res = await api.post("/daily/submit", payload);
            setSubmittedResult(res.data);
            setCompleted(true);
            if (res.data.score === 100) {
                fireConfetti();
            }
            toast.success(`Daily challenge complete! +${res.data.bonus_points} bonus XP`);
            // Re-fetch to get questions with answers
            const fresh = await api.get("/daily/challenge");
            setChallenge(fresh.data.challenge);
        } catch (err) {
            toast.error(err.response?.data?.detail || "Failed to submit");
        } finally {
            setSubmitting(false);
        }
    };

    const questions = challenge?.questions || [];

    return (
        <div className="min-h-screen bg-background">
            <header className="border-b border-border bg-card sticky top-0 z-10">
                <div className="container mx-auto px-4 py-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <Button variant="ghost" size="sm" onClick={() => navigate("/dashboard")} className="rounded-full">
                                <ArrowLeft className="w-5 h-5" />
                            </Button>
                            <Calendar className="w-8 h-8 text-amber-500" />
                            <span className="text-xl font-serif text-primary">Daily Challenge</span>
                        </div>
                        <DarkModeToggle />
                    </div>
                </div>
            </header>

            <div className="container mx-auto px-4 py-8 max-w-2xl">
                {loading ? (
                    <div className="text-center py-20">
                        <div className="inline-block w-8 h-8 border-4 border-accent border-t-transparent rounded-full animate-spin" />
                    </div>
                ) : (
                    <>
                        {/* Challenge header */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="text-center mb-8"
                        >
                            <div className="inline-flex items-center gap-2 bg-amber-100 dark:bg-amber-900/30 text-amber-800 dark:text-amber-200 px-4 py-2 rounded-full text-sm font-medium mb-4">
                                <Calendar className="w-4 h-4" />
                                {new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" })}
                            </div>
                            <h1 className="text-3xl font-serif text-primary mb-2">
                                {challenge?.subject} — {challenge?.topic}
                            </h1>
                            <p className="text-muted-foreground">
                                {completed ? "You've completed today's challenge!" : "Answer all 5 questions to earn bonus XP"}
                            </p>
                        </motion.div>

                        {/* Score if completed */}
                        {completed && submittedResult && (
                            <motion.div
                                initial={{ opacity: 0, scale: 0.9 }}
                                animate={{ opacity: 1, scale: 1 }}
                                className="bg-card rounded-2xl border border-border shadow-lg p-8 text-center mb-8"
                            >
                                <Trophy className="w-16 h-16 mx-auto text-amber-500 mb-4" />
                                <div className="text-5xl font-serif text-primary mb-2">
                                    {submittedResult.score?.toFixed(0)}%
                                </div>
                                <div className="text-muted-foreground">
                                    {submittedResult.correct_answers}/{submittedResult.total_questions} correct
                                    {submittedResult.bonus_points > 0 && (
                                        <span className="text-amber-600 font-semibold ml-2">
                                            +{submittedResult.bonus_points} bonus XP
                                        </span>
                                    )}
                                </div>
                            </motion.div>
                        )}

                        {/* Questions */}
                        <div className="space-y-6">
                            {questions.map((q, idx) => (
                                <motion.div
                                    key={q.id}
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: idx * 0.08 }}
                                    className="bg-card rounded-xl border border-border p-6 shadow-sm"
                                >
                                    <div className="flex items-start gap-3 mb-4">
                                        <div className="w-8 h-8 rounded-full bg-accent/10 flex items-center justify-center text-accent font-bold text-sm flex-shrink-0">
                                            {idx + 1}
                                        </div>
                                        <div className="font-medium text-primary">{q.question}</div>
                                    </div>

                                    {q.type === "mcq" && q.options ? (
                                        <div className="grid gap-2 ml-11">
                                            {q.options.map((opt, oi) => {
                                                const letter = opt.charAt(0);
                                                const isSelected = answers[q.id] === letter;
                                                const showResult = completed && submittedResult;
                                                const detail = submittedResult?.answers_detail?.find((a) => a.question_id === q.id);
                                                const isCorrectOpt = detail && detail.correct_answer?.toUpperCase() === letter.toUpperCase();
                                                const isWrongSelection = showResult && isSelected && !detail?.is_correct && detail?.user_answer?.toUpperCase() === letter.toUpperCase();

                                                return (
                                                    <button
                                                        key={oi}
                                                        type="button"
                                                        disabled={completed}
                                                        onClick={() => handleAnswer(q.id, letter)}
                                                        className={`text-left p-3 rounded-lg border-2 transition-all text-sm ${showResult && isCorrectOpt
                                                                ? "border-success bg-success/10 text-success"
                                                                : showResult && isWrongSelection
                                                                    ? "border-destructive bg-destructive/10 text-destructive"
                                                                    : isSelected
                                                                        ? "border-accent bg-accent/5"
                                                                        : "border-input hover:border-accent/40"
                                                            }`}
                                                    >
                                                        {opt}
                                                    </button>
                                                );
                                            })}
                                        </div>
                                    ) : (
                                        <div className="ml-11">
                                            <input
                                                type="text"
                                                disabled={completed}
                                                placeholder="Type your answer..."
                                                value={answers[q.id] || ""}
                                                onChange={(e) => handleAnswer(q.id, e.target.value)}
                                                className="w-full h-10 rounded-lg border-2 border-input bg-background px-3 text-sm"
                                            />
                                        </div>
                                    )}

                                    {/* Show explanation after completion */}
                                    {completed && q.explanation && (
                                        <div className="ml-11 mt-3 text-sm text-muted-foreground bg-muted/50 rounded-lg p-3">
                                            💡 {q.explanation}
                                        </div>
                                    )}
                                </motion.div>
                            ))}
                        </div>

                        {/* Submit */}
                        {!completed && questions.length > 0 && (
                            <Button
                                onClick={handleSubmit}
                                disabled={submitting || Object.keys(answers).length < questions.length}
                                className="w-full mt-8 bg-amber-500 hover:bg-amber-600 text-white rounded-full h-14 text-lg font-medium shadow-lg"
                            >
                                {submitting ? (
                                    <>
                                        <Clock className="w-5 h-5 mr-2 animate-spin" /> Submitting...
                                    </>
                                ) : (
                                    <>
                                        <Send className="w-5 h-5 mr-2" /> Submit Challenge
                                    </>
                                )}
                            </Button>
                        )}
                    </>
                )}
            </div>
        </div>
    );
}
