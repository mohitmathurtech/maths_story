import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import {
  Brain,
  Trophy,
  Zap,
  TrendingUp,
  Target,
  Play,
  BarChart3,
  Medal,
  LogOut,
  Shield,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import api from "@/utils/api";

export default function Dashboard({ user, onLogout }) {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    try {
      const response = await api.get("/analytics/dashboard");
      setStats(response.data);
    } catch (error) {
      toast.error("Failed to load dashboard");
    } finally {
      setLoading(false);
    }
  };

  const StatCard = ({ icon: Icon, label, value, color }) => (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className="bg-card rounded-xl border border-border/40 p-6 shadow-sm"
      data-testid={`stat-card-${label.toLowerCase().replace(/\s+/g, '-')}`}
    >
      <div className="flex items-start justify-between mb-3">
        <div className={`w-12 h-12 rounded-full flex items-center justify-center ${color}`}>
          <Icon className="w-6 h-6" strokeWidth={1.5} />
        </div>
      </div>
      <div className="text-3xl font-serif text-primary mb-1">{value}</div>
      <div className="text-sm text-muted-foreground">{label}</div>
    </motion.div>
  );

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-white sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Brain className="w-8 h-8 text-accent" />
              <span className="text-xl font-serif text-primary">Focus Learn</span>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right hidden sm:block">
                <div className="text-sm font-medium text-primary">{user?.name}</div>
                <div className="text-xs text-muted-foreground">
                  Level {user?.level} • {user?.points || 0} pts
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={onLogout}
                className="rounded-full"
                data-testid="logout-btn"
              >
                <LogOut className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        {/* Welcome Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-12"
        >
          <h1 className="text-4xl md:text-5xl font-serif text-primary mb-3" data-testid="dashboard-title">
            Welcome back, {user?.name?.split(" ")[0]}
          </h1>
          <p className="text-lg text-muted-foreground">
            Ready to sharpen your focus and master new concepts?
          </p>
        </motion.div>

        {loading ? (
          <div className="text-center py-20" data-testid="loading-state">
            <div className="inline-block w-8 h-8 border-4 border-accent border-t-transparent rounded-full animate-spin"></div>
          </div>
        ) : (
          <>
            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
              <StatCard
                icon={Trophy}
                label="Total Quizzes"
                value={stats?.total_quizzes || 0}
                color="bg-accent/10 text-accent"
              />
              <StatCard
                icon={Target}
                label="Avg Score"
                value={`${stats?.avg_score || 0}%`}
                color="bg-success/10 text-success"
              />
              <StatCard
                icon={Zap}
                label="Focus Score"
                value={stats?.avg_focus || 0}
                color="bg-amber-100 text-amber-600"
              />
              <StatCard
                icon={Medal}
                label="Total Points"
                value={stats?.points || 0}
                color="bg-purple-100 text-purple-600"
              />
            </div>

            {/* Action Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
              <motion.div
                whileHover={{ scale: 1.02, y: -4 }}
                onClick={() => navigate("/quiz/select")}
                className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-xl p-8 text-white cursor-pointer shadow-lg"
                data-testid="start-quiz-card"
              >
                <Play className="w-10 h-10 mb-4" />
                <h3 className="text-2xl font-serif mb-2">Start Quiz</h3>
                <p className="text-slate-300">Choose a topic and test your knowledge</p>
              </motion.div>

              <motion.div
                whileHover={{ scale: 1.02, y: -4 }}
                onClick={() => navigate("/analytics")}
                className="bg-card border-2 border-accent/20 rounded-xl p-8 cursor-pointer shadow-sm"
                data-testid="analytics-card"
              >
                <BarChart3 className="w-10 h-10 text-accent mb-4" />
                <h3 className="text-2xl font-serif text-primary mb-2">Analytics</h3>
                <p className="text-muted-foreground">Track your progress and insights</p>
              </motion.div>

              <motion.div
                whileHover={{ scale: 1.02, y: -4 }}
                onClick={() => navigate("/leaderboard")}
                className="bg-card border-2 border-amber-200 rounded-xl p-8 cursor-pointer shadow-sm"
                data-testid="leaderboard-card"
              >
                <TrendingUp className="w-10 h-10 text-amber-600 mb-4" />
                <h3 className="text-2xl font-serif text-primary mb-2">Leaderboard</h3>
                <p className="text-muted-foreground">See how you rank globally</p>
              </motion.div>
            </div>

            {/* Recent Activity */}
            {stats?.recent_results && stats.recent_results.length > 0 && (
              <div>
                <h2 className="text-2xl font-serif text-primary mb-6">Recent Activity</h2>
                <div className="space-y-3">
                  {stats.recent_results.map((result, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="bg-card border border-border/40 rounded-lg p-5 flex items-center justify-between hover:shadow-md transition-shadow"
                      data-testid={`recent-result-${index}`}
                    >
                      <div>
                        <div className="font-medium text-primary">
                          {result.subject} - {result.topic}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          {new Date(result.created_at).toLocaleDateString()}
                        </div>
                      </div>
                      <div className="flex items-center gap-6">
                        <div className="text-right">
                          <div className="text-lg font-semibold text-success">
                            {result.score.toFixed(0)}%
                          </div>
                          <div className="text-xs text-muted-foreground">Score</div>
                        </div>
                        <div className="text-right">
                          <div className="text-lg font-semibold text-accent">
                            {result.focus_score.toFixed(0)}
                          </div>
                          <div className="text-xs text-muted-foreground">Focus</div>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}