import { useEffect, useState, useRef } from "react";
import { motion } from "framer-motion";
import { useNavigate, useParams } from "react-router-dom";
import {
  Trophy,
  Target,
  Clock,
  Zap,
  CheckCircle,
  XCircle,
  ArrowRight,
  Home,
  Share2,
  Copy,
  ChevronDown,
  ChevronUp,
  BookOpen,
  History,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import DarkModeToggle from "@/components/DarkModeToggle";
import {
  playQuizCompleteSound,
  fireConfetti,
  firePerfectScoreConfetti,
} from "@/utils/sounds";

export default function Results({ user }) {
  const { resultId } = useParams();
  const navigate = useNavigate();
  const [result, setResult] = useState(null);
  const [expandedQ, setExpandedQ] = useState(null);
  const soundPlayed = useRef(false);

  useEffect(() => {
    const storedResult = sessionStorage.getItem("quizResult");
    if (storedResult) {
      setResult(JSON.parse(storedResult));
    } else {
      navigate("/dashboard");
    }
  }, [resultId, navigate]);

  // Fire confetti & sound once
  useEffect(() => {
    if (result && !soundPlayed.current) {
      soundPlayed.current = true;
      setTimeout(() => {
        playQuizCompleteSound();
        if (result.score === 100) {
          firePerfectScoreConfetti();
        } else if (result.score >= 60) {
          fireConfetti();
        }
      }, 400);
    }
  }, [result]);

  if (!result) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="inline-block w-10 h-10 border-4 border-accent border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  const scoreColor =
    result.score >= 80
      ? "text-success"
      : result.score >= 60
        ? "text-amber-600"
        : "text-destructive";

  const handleShare = async () => {
    const shareText = `🎯 I scored ${result.score.toFixed(0)}% on ${result.subject} — ${result.topic} on Focus Learn!`;
    const shareUrl = `${window.location.origin}/results/${result.id}`;

    if (navigator.share) {
      try {
        await navigator.share({ title: "Focus Learn Results", text: shareText, url: shareUrl });
      } catch { }
    } else {
      navigator.clipboard.writeText(`${shareText}\n${shareUrl}`);
      toast.success("Result link copied to clipboard!");
    }
  };

  // Use answers_detail (new detailed breakdown) or fall back to explanations
  const hasDetail = result.answers_detail && result.answers_detail.length > 0;
  const reviewItems = hasDetail
    ? result.answers_detail
    : result.explanations || [];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-indigo-50 dark:from-slate-900 dark:via-slate-900 dark:to-indigo-950">
      <div className="container mx-auto px-4 py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="max-w-3xl mx-auto"
        >
          {/* Top bar */}
          <div className="flex justify-end mb-4">
            <DarkModeToggle />
          </div>

          {/* Score Card */}
          <div className="bg-card rounded-2xl border border-border shadow-xl p-10 mb-8 text-center">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.2, type: "spring" }}
              className="mb-6"
            >
              <Trophy className="w-20 h-20 mx-auto text-accent mb-4" />
              <h1
                className="text-5xl font-serif text-primary mb-2"
                data-testid="quiz-complete-title"
              >
                {result.score === 100 ? "🎉 Perfect Score!" : "Quiz Complete!"}
              </h1>
              <p className="text-muted-foreground text-lg">
                {result.subject} - {result.topic}
              </p>
            </motion.div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mt-10">
              <div className="space-y-2">
                <div
                  className={`text-4xl font-serif ${scoreColor}`}
                  data-testid="score-value"
                >
                  {result.score.toFixed(0)}%
                </div>
                <div className="text-sm text-muted-foreground">Score</div>
              </div>
              <div className="space-y-2">
                <div
                  className="text-4xl font-serif text-accent"
                  data-testid="focus-score-value"
                >
                  {result.focus_score.toFixed(0)}
                </div>
                <div className="text-sm text-muted-foreground">Focus</div>
              </div>
              <div className="space-y-2">
                <div className="text-4xl font-serif text-primary">
                  {result.correct_answers}/{result.total_questions}
                </div>
                <div className="text-sm text-muted-foreground">Correct</div>
              </div>
              <div className="space-y-2">
                <div className="text-4xl font-serif text-primary">
                  +{result.points_earned}
                </div>
                <div className="text-sm text-muted-foreground">Points</div>
              </div>
            </div>
          </div>

          {/* Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <div className="bg-card rounded-xl border border-border p-6">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-full bg-success/10 flex items-center justify-center">
                  <Target className="w-5 h-5 text-success" />
                </div>
                <div className="font-medium text-primary">Accuracy</div>
              </div>
              <div className="text-2xl font-serif text-primary">
                {result.score.toFixed(1)}%
              </div>
            </div>

            <div className="bg-card rounded-xl border border-border p-6">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-full bg-accent/10 flex items-center justify-center">
                  <Clock className="w-5 h-5 text-accent" />
                </div>
                <div className="font-medium text-primary">Avg Time</div>
              </div>
              <div className="text-2xl font-serif text-primary">
                {result.avg_time.toFixed(1)}s
              </div>
            </div>

            <div className="bg-card rounded-xl border border-border p-6">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-full bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
                  <Zap className="w-5 h-5 text-amber-600" />
                </div>
                <div className="font-medium text-primary">Consistency</div>
              </div>
              <div className="text-2xl font-serif text-primary">
                {result.focus_score > 80
                  ? "High"
                  : result.focus_score > 60
                    ? "Medium"
                    : "Low"}
              </div>
            </div>
          </div>

          {/* Detailed Question Review */}
          {reviewItems.length > 0 && (
            <div className="bg-card rounded-2xl border border-border shadow-lg p-8 mb-8">
              <div className="flex items-center gap-2 mb-6">
                <BookOpen className="w-5 h-5 text-accent" />
                <h2 className="text-2xl font-serif text-primary">
                  Question Review
                </h2>
              </div>
              <div className="space-y-4">
                {reviewItems.map((item, index) => {
                  const isCorrect = hasDetail
                    ? item.is_correct
                    : true; // Legacy fallback
                  const isExpanded = expandedQ === index;

                  return (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className={`rounded-xl border-2 overflow-hidden transition-colors ${isCorrect
                          ? "border-success/30 bg-success/5"
                          : "border-destructive/30 bg-destructive/5"
                        }`}
                    >
                      {/* Question header */}
                      <button
                        onClick={() =>
                          setExpandedQ(isExpanded ? null : index)
                        }
                        className="w-full text-left p-4 flex items-center gap-3"
                      >
                        <div className="flex-shrink-0">
                          {isCorrect ? (
                            <CheckCircle className="w-6 h-6 text-success" />
                          ) : (
                            <XCircle className="w-6 h-6 text-destructive" />
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-primary text-sm">
                            Q{index + 1}: {item.question}
                          </div>
                          {hasDetail && (
                            <div className="flex gap-4 mt-1 text-xs text-muted-foreground">
                              <span>
                                Your answer:{" "}
                                <span
                                  className={
                                    isCorrect
                                      ? "text-success font-semibold"
                                      : "text-destructive font-semibold"
                                  }
                                >
                                  {item.user_answer}
                                </span>
                              </span>
                              {!isCorrect && (
                                <span>
                                  Correct:{" "}
                                  <span className="text-success font-semibold">
                                    {item.correct_answer}
                                  </span>
                                </span>
                              )}
                              {item.time_taken && (
                                <span>{item.time_taken.toFixed(1)}s</span>
                              )}
                            </div>
                          )}
                        </div>
                        <div className="flex-shrink-0">
                          {isExpanded ? (
                            <ChevronUp className="w-5 h-5 text-muted-foreground" />
                          ) : (
                            <ChevronDown className="w-5 h-5 text-muted-foreground" />
                          )}
                        </div>
                      </button>

                      {/* Expandable explanation */}
                      {isExpanded && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: "auto", opacity: 1 }}
                          className="px-4 pb-4"
                        >
                          <div className="bg-card rounded-lg p-4 border border-border">
                            {hasDetail && !isCorrect && (
                              <div className="mb-3 text-sm">
                                <span className="font-semibold text-primary">
                                  Correct Answer:{" "}
                                </span>
                                <span className="text-success font-medium">
                                  {item.correct_answer}
                                </span>
                              </div>
                            )}
                            {(item.explanation ||
                              (hasDetail && item.explanation)) && (
                                <div className="text-sm text-muted-foreground leading-relaxed">
                                  <span className="font-semibold text-primary">
                                    Explanation:{" "}
                                  </span>
                                  {item.explanation}
                                </div>
                              )}
                            {item.story_context && (
                              <div className="mt-2 text-sm italic text-accent">
                                📖 {item.story_context}
                              </div>
                            )}
                            {item.hint && (
                              <div className="mt-2 text-sm text-amber-600">
                                💡 Hint: {item.hint}
                              </div>
                            )}
                          </div>
                        </motion.div>
                      )}
                    </motion.div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex flex-col sm:flex-row gap-4">
            <Button
              onClick={() => {
                sessionStorage.removeItem("quizResult");
                navigate("/quiz/select");
              }}
              className="flex-1 bg-primary text-primary-foreground hover:bg-primary/90 rounded-full h-12 font-medium shadow-md hover:scale-105 active:scale-95 transition-transform"
              data-testid="take-another-btn"
            >
              Take Another Quiz
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
            <Button
              onClick={handleShare}
              variant="outline"
              className="flex-1 border-2 rounded-full h-12 font-medium"
            >
              <Share2 className="w-5 h-5 mr-2" />
              Share Result
            </Button>
            <Button
              onClick={() => {
                sessionStorage.removeItem("quizResult");
                navigate("/quiz-history");
              }}
              variant="outline"
              className="flex-1 border-2 rounded-full h-12 font-medium"
            >
              <History className="w-5 h-5 mr-2" />
              View History
            </Button>
            <Button
              onClick={() => {
                sessionStorage.removeItem("quizResult");
                navigate("/dashboard");
              }}
              variant="outline"
              className="flex-1 border-2 rounded-full h-12 font-medium"
              data-testid="back-dashboard-btn"
            >
              <Home className="w-5 h-5 mr-2" />
              Dashboard
            </Button>
          </div>
        </motion.div>
      </div>
    </div>
  );
}