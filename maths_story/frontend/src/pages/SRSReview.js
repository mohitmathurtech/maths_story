import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import {
    Brain,
    ArrowLeft,
    BookOpen,
    CheckCircle,
    XCircle,
    SkipForward,
    BarChart3,
    Layers,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import api from "@/utils/api";
import DarkModeToggle from "@/components/DarkModeToggle";
import { playCorrectSound, playWrongSound } from "@/utils/sounds";

export default function SRSReview({ user, onLogout }) {
    const navigate = useNavigate();
    const [cards, setCards] = useState([]);
    const [stats, setStats] = useState(null);
    const [currentIdx, setCurrentIdx] = useState(0);
    const [answer, setAnswer] = useState("");
    const [showResult, setShowResult] = useState(false);
    const [lastResult, setLastResult] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            const [cardsRes, statsRes] = await Promise.all([
                api.get("/srs/review?limit=20"),
                api.get("/srs/stats"),
            ]);
            setCards(cardsRes.data.cards);
            setStats(statsRes.data);
        } catch (err) {
            toast.error("Failed to load review cards");
        } finally {
            setLoading(false);
        }
    };

    const currentCard = cards[currentIdx];

    const handleSubmit = async () => {
        if (!answer.trim()) {
            toast.error("Please provide an answer");
            return;
        }

        try {
            const res = await api.post(`/srs/review/${currentCard.id}`, {
                user_answer: answer,
                time_taken: 0,
            });
            setLastResult(res.data);
            setShowResult(true);

            if (res.data.is_correct) {
                playCorrectSound();
            } else {
                playWrongSound();
            }
        } catch (err) {
            toast.error("Failed to submit review");
        }
    };

    const handleNext = () => {
        setShowResult(false);
        setLastResult(null);
        setAnswer("");
        if (currentIdx + 1 < cards.length) {
            setCurrentIdx(currentIdx + 1);
        } else {
            toast.success("Review session complete! 🎉");
            fetchData(); // Refresh
            setCurrentIdx(0);
        }
    };

    const bucketLabels = ["Learning", "Familiar", "Reviewing", "Known", "Mastered"];

    return (
        <div className="min-h-screen bg-background">
            <header className="border-b border-border bg-card sticky top-0 z-10">
                <div className="container mx-auto px-4 py-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <Button variant="ghost" size="sm" onClick={() => navigate("/dashboard")} className="rounded-full">
                                <ArrowLeft className="w-5 h-5" />
                            </Button>
                            <BookOpen className="w-8 h-8 text-emerald-600" />
                            <span className="text-xl font-serif text-primary">SRS Review</span>
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
                        {/* Stats Bar */}
                        {stats && (
                            <div className="grid grid-cols-3 gap-4 mb-8">
                                <div className="bg-card rounded-xl border border-border p-4 text-center">
                                    <div className="text-2xl font-serif text-primary">{stats.due_now}</div>
                                    <div className="text-xs text-muted-foreground">Due Now</div>
                                </div>
                                <div className="bg-card rounded-xl border border-border p-4 text-center">
                                    <div className="text-2xl font-serif text-primary">{stats.total_cards}</div>
                                    <div className="text-xs text-muted-foreground">Total Cards</div>
                                </div>
                                <div className="bg-card rounded-xl border border-border p-4 text-center">
                                    <div className="text-2xl font-serif text-emerald-600">{stats.mastered}</div>
                                    <div className="text-xs text-muted-foreground">Mastered</div>
                                </div>
                            </div>
                        )}

                        {/* Bucket distribution */}
                        {stats && stats.total_cards > 0 && (
                            <div className="bg-card rounded-xl border border-border p-4 mb-8">
                                <div className="flex items-center gap-2 mb-3">
                                    <Layers className="w-4 h-4 text-muted-foreground" />
                                    <span className="text-sm font-medium text-primary">Leitner Boxes</span>
                                </div>
                                <div className="flex gap-2">
                                    {[0, 1, 2, 3, 4].map((b) => (
                                        <div key={b} className="flex-1 text-center">
                                            <div
                                                className={`h-2 rounded-full mb-1 ${b === 4
                                                        ? "bg-emerald-500"
                                                        : b >= 2
                                                            ? "bg-amber-400"
                                                            : "bg-orange-400"
                                                    }`}
                                                style={{
                                                    opacity: Math.max(0.2, (stats.bucket_distribution?.[String(b)] || 0) / Math.max(stats.total_cards, 1)),
                                                }}
                                            />
                                            <div className="text-xs text-muted-foreground">{bucketLabels[b]}</div>
                                            <div className="text-xs font-medium text-primary">
                                                {stats.bucket_distribution?.[String(b)] || 0}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Current Card */}
                        {cards.length === 0 ? (
                            <motion.div
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                className="text-center py-16"
                            >
                                <CheckCircle className="w-16 h-16 mx-auto text-emerald-500 mb-4" />
                                <h2 className="text-2xl font-serif text-primary mb-2">All Caught Up!</h2>
                                <p className="text-muted-foreground mb-6">
                                    No cards due for review right now. Take a quiz to add questions to your review queue.
                                </p>
                                <Button onClick={() => navigate("/quiz/select")} className="rounded-full">
                                    Take a Quiz
                                </Button>
                            </motion.div>
                        ) : currentCard ? (
                            <motion.div
                                key={currentCard.id}
                                initial={{ opacity: 0, x: 30 }}
                                animate={{ opacity: 1, x: 0 }}
                                className="bg-card rounded-2xl border-2 border-border shadow-lg p-8"
                            >
                                {/* Progress */}
                                <div className="flex items-center justify-between mb-6 text-sm text-muted-foreground">
                                    <span>
                                        Card {currentIdx + 1} of {cards.length}
                                    </span>
                                    <span className="bg-muted px-2 py-1 rounded text-xs">
                                        {currentCard.subject} — {currentCard.topic}
                                    </span>
                                </div>

                                {/* Question */}
                                <div className="text-lg font-medium text-primary mb-6">
                                    {currentCard.question?.question}
                                </div>

                                {/* MCQ Options or Text Input */}
                                {!showResult && (
                                    <>
                                        {currentCard.question?.type === "mcq" && currentCard.question?.options ? (
                                            <div className="grid gap-2 mb-6">
                                                {currentCard.question.options.map((opt, oi) => {
                                                    const letter = opt.charAt(0);
                                                    return (
                                                        <button
                                                            key={oi}
                                                            type="button"
                                                            onClick={() => setAnswer(letter)}
                                                            className={`text-left p-3 rounded-lg border-2 transition-all text-sm ${answer === letter
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
                                            <input
                                                type="text"
                                                placeholder="Type your answer..."
                                                value={answer}
                                                onChange={(e) => setAnswer(e.target.value)}
                                                onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
                                                className="w-full h-12 rounded-lg border-2 border-input bg-background px-4 text-base mb-6"
                                            />
                                        )}

                                        <Button
                                            onClick={handleSubmit}
                                            disabled={!answer.trim()}
                                            className="w-full rounded-full h-12 font-medium"
                                        >
                                            Check Answer
                                        </Button>
                                    </>
                                )}

                                {/* Result */}
                                {showResult && lastResult && (
                                    <motion.div
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                    >
                                        <div
                                            className={`rounded-xl p-4 mb-4 ${lastResult.is_correct
                                                    ? "bg-success/10 border border-success/30"
                                                    : "bg-destructive/10 border border-destructive/30"
                                                }`}
                                        >
                                            <div className="flex items-center gap-2 mb-2">
                                                {lastResult.is_correct ? (
                                                    <>
                                                        <CheckCircle className="w-5 h-5 text-success" />
                                                        <span className="font-medium text-success">Correct! +{lastResult.points_earned} pts</span>
                                                    </>
                                                ) : (
                                                    <>
                                                        <XCircle className="w-5 h-5 text-destructive" />
                                                        <span className="font-medium text-destructive">
                                                            Incorrect — Answer: {lastResult.correct_answer}
                                                        </span>
                                                    </>
                                                )}
                                            </div>
                                            {lastResult.explanation && (
                                                <p className="text-sm text-muted-foreground">{lastResult.explanation}</p>
                                            )}
                                            <div className="text-xs text-muted-foreground mt-2">
                                                Next review: Bucket {lastResult.new_bucket} ({bucketLabels[lastResult.new_bucket]})
                                            </div>
                                        </div>

                                        <Button
                                            onClick={handleNext}
                                            className="w-full rounded-full h-12 font-medium"
                                        >
                                            {currentIdx + 1 < cards.length ? (
                                                <>Next Card <SkipForward className="w-4 h-4 ml-2" /></>
                                            ) : (
                                                "Finish Session"
                                            )}
                                        </Button>
                                    </motion.div>
                                )}
                            </motion.div>
                        ) : null}
                    </>
                )}
            </div>
        </div>
    );
}
