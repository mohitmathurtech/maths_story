import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { Brain, ArrowLeft, Trophy, Medal, Award } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import api from "@/utils/api";

export default function Leaderboard({ user }) {
  const navigate = useNavigate();
  const [leaderboard, setLeaderboard] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLeaderboard();
  }, []);

  const fetchLeaderboard = async () => {
    try {
      const response = await api.get("/leaderboard");
      setLeaderboard(response.data);
    } catch (error) {
      toast.error("Failed to load leaderboard");
    } finally {
      setLoading(false);
    }
  };

  const getMedalIcon = (rank) => {
    if (rank === 1) return <Trophy className="w-7 h-7 text-amber-500" />;
    if (rank === 2) return <Medal className="w-7 h-7 text-slate-400" />;
    if (rank === 3) return <Award className="w-7 h-7 text-amber-700" />;
    return null;
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
          <h1 className="text-4xl md:text-5xl font-serif text-primary mb-3" data-testid="leaderboard-title">
            Global Leaderboard
          </h1>
          <p className="text-lg text-muted-foreground">
            See how you rank against other learners
          </p>
        </motion.div>

        {loading ? (
          <div className="text-center py-20" data-testid="loading-state">
            <div className="inline-block w-8 h-8 border-4 border-accent border-t-transparent rounded-full animate-spin"></div>
          </div>
        ) : (
          <div className="max-w-3xl mx-auto">
            {leaderboard.length > 0 ? (
              <div className="bg-white rounded-2xl border border-border shadow-lg overflow-hidden">
                <div className="divide-y divide-border">
                  {leaderboard.map((player, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className={`p-6 flex items-center justify-between hover:bg-slate-50 transition-colors ${
                        player.id === user?.id ? "bg-accent/5" : ""
                      }`}
                      data-testid={`leaderboard-item-${index}`}
                    >
                      <div className="flex items-center gap-4">
                        <div className="w-12 text-center">
                          {index < 3 ? (
                            getMedalIcon(index + 1)
                          ) : (
                            <span className="text-xl font-serif text-muted-foreground">
                              {index + 1}
                            </span>
                          )}
                        </div>
                        <div>
                          <div className="font-semibold text-primary">
                            {player.name}
                            {player.id === user?.id && (
                              <span className="ml-2 text-xs bg-accent/10 text-accent px-2 py-1 rounded-full">
                                You
                              </span>
                            )}
                          </div>
                          <div className="text-sm text-muted-foreground">
                            Level {player.level}
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-serif text-accent">
                          {player.points}
                        </div>
                        <div className="text-xs text-muted-foreground">points</div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-2xl border border-border shadow-lg p-12 text-center">
                <Trophy className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-xl font-serif text-primary mb-2">
                  No Rankings Yet
                </h3>
                <p className="text-muted-foreground mb-6">
                  Be the first to complete quizzes and claim the top spot!
                </p>
                <Button
                  onClick={() => navigate("/quiz/select")}
                  className="bg-primary text-primary-foreground hover:bg-primary/90 rounded-full px-8 py-3"
                  data-testid="start-quiz-btn"
                >
                  Start a Quiz
                </Button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}