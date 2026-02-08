import { useEffect, useState } from "react";
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
} from "lucide-react";
import { Button } from "@/components/ui/button";

export default function Results({ user }) {
  const { resultId } = useParams();
  const navigate = useNavigate();
  const [result, setResult] = useState(null);

  useEffect(() => {
    const storedResult = sessionStorage.getItem("quizResult");
    if (storedResult) {
      setResult(JSON.parse(storedResult));
    } else {
      navigate("/dashboard");
    }
  }, [resultId, navigate]);

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

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-indigo-50">
      <div className="container mx-auto px-4 py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="max-w-3xl mx-auto"
        >
          {/* Score Card */}
          <div className="bg-white rounded-2xl border border-border shadow-xl p-10 mb-8 text-center">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.2, type: "spring" }}
              className="mb-6"
            >
              <Trophy className="w-20 h-20 mx-auto text-accent mb-4" />
              <h1 className="text-5xl font-serif text-primary mb-2" data-testid="quiz-complete-title">
                Quiz Complete!
              </h1>
              <p className="text-muted-foreground text-lg">
                {result.subject} - {result.topic}
              </p>
            </motion.div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mt-10">
              <div className="space-y-2">
                <div className={`text-4xl font-serif ${scoreColor}`} data-testid="score-value">
                  {result.score.toFixed(0)}%
                </div>
                <div className="text-sm text-muted-foreground">Score</div>
              </div>
              <div className="space-y-2">
                <div className="text-4xl font-serif text-accent" data-testid="focus-score-value">
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
            <div className="bg-white rounded-xl border border-border p-6">
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

            <div className="bg-white rounded-xl border border-border p-6">
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

            <div className="bg-white rounded-xl border border-border p-6">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-full bg-amber-100 flex items-center justify-center">
                  <Zap className="w-5 h-5 text-amber-600" />
                </div>
                <div className="font-medium text-primary">Consistency</div>
              </div>
              <div className="text-2xl font-serif text-primary">
                {result.focus_score > 80 ? "High" : result.focus_score > 60 ? "Medium" : "Low"}
              </div>
            </div>
          </div>

          {/* Explanations */}
          {result.explanations && result.explanations.length > 0 && (
            <div className="bg-white rounded-2xl border border-border shadow-lg p-8 mb-8">
              <h2 className="text-2xl font-serif text-primary mb-6">Review Questions</h2>
              <div className="space-y-6">
                {result.explanations.map((item, index) => (
                  <div
                    key={index}
                    className="border-l-4 border-accent/30 pl-6 py-2"
                    data-testid={`explanation-${index}`}
                  >
                    <div className="flex items-start gap-3 mb-2">
                      <div className="mt-1">
                        <CheckCircle className="w-5 h-5 text-success" />
                      </div>
                      <div className="flex-1">
                        <div className="font-medium text-primary mb-2">
                          {item.question}
                        </div>
                        <div className="text-sm text-muted-foreground mb-2">
                          <span className="font-semibold">Correct Answer:</span>{" "}
                          {item.correct_answer}
                        </div>
                        {item.explanation && (
                          <div className="text-sm text-muted-foreground bg-slate-50 rounded-lg p-3">
                            {item.explanation}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
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
              onClick={() => {
                sessionStorage.removeItem("quizResult");
                navigate("/dashboard");
              }}
              variant="outline"
              className="flex-1 border-2 rounded-full h-12 font-medium"
              data-testid="back-dashboard-btn"
            >
              <Home className="w-5 h-5 mr-2" />
              Back to Dashboard
            </Button>
          </div>
        </motion.div>
      </div>
    </div>
  );
}