import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { Brain, ArrowLeft, TrendingUp, Target } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import api from "@/utils/api";

export default function Analytics({ user }) {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      const response = await api.get("/analytics/dashboard");
      setStats(response.data);
    } catch (error) {
      toast.error("Failed to load analytics");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-white">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate("/dashboard")}
                className="rounded-full"
                data-testid="back-btn"
              >
                <ArrowLeft className="w-5 h-5" />
              </Button>
              <Brain className="w-8 h-8 text-accent" />
              <span className="text-xl font-serif text-primary">Focus Learn</span>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-10"
        >
          <h1 className="text-4xl md:text-5xl font-serif text-primary mb-3" data-testid="analytics-title">
            Your Analytics
          </h1>
          <p className="text-lg text-muted-foreground">
            Track your progress and identify areas for improvement
          </p>
        </motion.div>

        {loading ? (
          <div className="text-center py-20" data-testid="loading-state">
            <div className="inline-block w-8 h-8 border-4 border-accent border-t-transparent rounded-full animate-spin"></div>
          </div>
        ) : (
          <>
            {/* Overall Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12">
              <div className="bg-white rounded-xl border border-border p-6 shadow-sm">
                <div className="text-sm text-muted-foreground mb-2">Total Quizzes</div>
                <div className="text-3xl font-serif text-primary" data-testid="total-quizzes">
                  {stats?.total_quizzes || 0}
                </div>
              </div>
              <div className="bg-white rounded-xl border border-border p-6 shadow-sm">
                <div className="text-sm text-muted-foreground mb-2">Average Score</div>
                <div className="text-3xl font-serif text-success" data-testid="avg-score">
                  {stats?.avg_score || 0}%
                </div>
              </div>
              <div className="bg-white rounded-xl border border-border p-6 shadow-sm">
                <div className="text-sm text-muted-foreground mb-2">Focus Score</div>
                <div className="text-3xl font-serif text-accent" data-testid="avg-focus">
                  {stats?.avg_focus || 0}
                </div>
              </div>
              <div className="bg-white rounded-xl border border-border p-6 shadow-sm">
                <div className="text-sm text-muted-foreground mb-2">Current Level</div>
                <div className="text-3xl font-serif text-primary" data-testid="user-level">
                  {stats?.level || 1}
                </div>
              </div>
            </div>

            {/* Topic Performance */}
            {stats?.topic_performance && stats.topic_performance.length > 0 ? (
              <div className="bg-white rounded-2xl border border-border shadow-lg p-8">
                <div className="flex items-center gap-3 mb-6">
                  <TrendingUp className="w-6 h-6 text-accent" />
                  <h2 className="text-2xl font-serif text-primary">Topic Performance</h2>
                </div>
                <div className="space-y-4">
                  {stats.topic_performance.map((topic, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="border border-border rounded-xl p-5 hover:shadow-md transition-shadow"
                      data-testid={`topic-${index}`}
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div>
                          <div className="font-semibold text-primary">
                            {topic.subject} - {topic.topic}
                          </div>
                          <div className="text-sm text-muted-foreground">
                            {topic.attempts} attempt{topic.attempts !== 1 ? "s" : ""}
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-2xl font-serif text-success">
                            {topic.avg_score.toFixed(0)}%
                          </div>
                        </div>
                      </div>
                      <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${topic.avg_score}%` }}
                          transition={{ delay: index * 0.1 + 0.2, duration: 0.5 }}
                          className="h-full bg-success rounded-full"
                        />
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-2xl border border-border shadow-lg p-12 text-center">
                <Target className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-xl font-serif text-primary mb-2">
                  No Data Yet
                </h3>
                <p className="text-muted-foreground mb-6">
                  Complete some quizzes to see your performance analytics
                </p>
                <Button
                  onClick={() => navigate("/quiz/select")}
                  className="bg-primary text-primary-foreground hover:bg-primary/90 rounded-full px-8 py-3"
                  data-testid="start-first-quiz-btn"
                >
                  Start Your First Quiz
                </Button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}