import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import {
  Brain,
  ArrowLeft,
  User,
  Mail,
  Trophy,
  Zap,
  Target,
  Flame,
  Star,
  Medal,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import api from "@/utils/api";
import DarkModeToggle from "@/components/DarkModeToggle";

const tierColors = {
  gold: "bg-amber-100 dark:bg-amber-900/30 border-amber-400 text-amber-700 dark:text-amber-300",
  silver: "bg-slate-100 dark:bg-slate-700/30 border-slate-400 text-slate-700 dark:text-slate-300",
  bronze: "bg-orange-100 dark:bg-orange-900/30 border-orange-400 text-orange-700 dark:text-orange-300",
  locked: "bg-muted border-border text-muted-foreground opacity-50",
};

export default function Profile({ user, onLogout }) {
  const navigate = useNavigate();
  const [achievements, setAchievements] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAchievements();
  }, []);

  const fetchAchievements = async () => {
    try {
      const res = await api.get("/analytics/achievements");
      setAchievements(res.data);
    } catch {
      // Silently fail — profile still works without achievements
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate("/dashboard")}
                className="rounded-full"
              >
                <ArrowLeft className="w-5 h-5" />
              </Button>
              <Brain className="w-8 h-8 text-accent" />
              <span className="text-xl font-serif text-primary">Profile</span>
            </div>
            <DarkModeToggle />
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8 max-w-2xl">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          {/* User Card */}
          <div className="bg-card rounded-2xl border border-border shadow-lg p-8 mb-6">
            <div className="flex items-center gap-6 mb-8">
              <div className="w-20 h-20 rounded-full bg-gradient-to-br from-accent/20 to-accent/5 flex items-center justify-center border-2 border-accent/30">
                <User className="w-10 h-10 text-accent" />
              </div>
              <div className="flex-1">
                <h2 className="text-2xl font-serif text-primary">{user?.name}</h2>
                <div className="flex items-center gap-2 text-muted-foreground text-sm">
                  <Mail className="w-3.5 h-3.5" />
                  <span>{user?.email}</span>
                </div>
                <div className="flex items-center gap-3 mt-2">
                  <span className="bg-accent/10 text-accent text-xs px-2 py-1 rounded-full font-medium">
                    Level {achievements?.level || user?.level || 1}
                  </span>
                  <span className="flex items-center gap-1 text-amber-600 text-xs font-medium">
                    <Flame className="w-3.5 h-3.5" />
                    {achievements?.streak || 0} day streak
                  </span>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-4 gap-4 pt-6 border-t border-border">
              <div className="text-center">
                <div className="text-2xl font-serif text-primary">
                  {achievements?.total_quizzes || 0}
                </div>
                <div className="text-xs text-muted-foreground">Quizzes</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-serif text-accent">
                  {achievements?.points || user?.points || 0}
                </div>
                <div className="text-xs text-muted-foreground">Points</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-serif text-success">
                  {achievements?.total_correct || 0}
                </div>
                <div className="text-xs text-muted-foreground">Correct</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-serif text-amber-600">
                  {achievements?.perfect_scores || 0}
                </div>
                <div className="text-xs text-muted-foreground">Perfect</div>
              </div>
            </div>
          </div>

          {/* Badges */}
          {achievements?.badges && (
            <div className="bg-card rounded-2xl border border-border shadow-lg p-6 mb-6">
              <div className="flex items-center gap-2 mb-5">
                <Medal className="w-5 h-5 text-accent" />
                <h3 className="text-xl font-serif text-primary">Badges</h3>
              </div>
              <div className="grid grid-cols-2 gap-3">
                {achievements.badges.map((badge) => (
                  <motion.div
                    key={badge.id}
                    whileHover={{ scale: 1.02 }}
                    className={`rounded-xl border-2 p-4 transition-all ${tierColors[badge.tier] || tierColors.locked
                      }`}
                  >
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-2xl">{badge.icon}</span>
                      <div className="flex-1">
                        <div className="text-sm font-semibold">{badge.name}</div>
                        <div className="text-xs opacity-70">{badge.desc}</div>
                      </div>
                      {badge.tier !== "locked" && (
                        <span className="text-xs font-bold uppercase">
                          {badge.tier}
                        </span>
                      )}
                    </div>
                    {/* Progress bar */}
                    <div className="w-full h-1.5 rounded-full bg-black/10 dark:bg-white/10 overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${badge.tier === "gold"
                            ? "bg-amber-500"
                            : badge.tier === "silver"
                              ? "bg-slate-400"
                              : badge.tier === "bronze"
                                ? "bg-orange-400"
                                : "bg-muted-foreground/30"
                          }`}
                        style={{
                          width: `${Math.min(
                            100,
                            (badge.progress / badge.next_at) * 100
                          )}%`,
                        }}
                      />
                    </div>
                    <div className="text-xs mt-1 opacity-60">
                      {badge.progress}/{badge.next_at}
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          )}

          {/* Milestones */}
          {achievements?.milestones && (
            <div className="bg-card rounded-2xl border border-border shadow-lg p-6 mb-6">
              <div className="flex items-center gap-2 mb-4">
                <Star className="w-5 h-5 text-amber-500" />
                <h3 className="text-xl font-serif text-primary">Milestones</h3>
              </div>
              <div className="space-y-2">
                {achievements.milestones.map((m, i) => (
                  <div
                    key={i}
                    className={`flex items-center gap-3 p-3 rounded-lg ${m.reached
                        ? "bg-success/5 border border-success/20"
                        : "bg-muted/30 border border-border"
                      }`}
                  >
                    <div
                      className={`w-6 h-6 rounded-full flex items-center justify-center text-xs ${m.reached
                          ? "bg-success text-white"
                          : "bg-muted text-muted-foreground"
                        }`}
                    >
                      {m.reached ? "✓" : "—"}
                    </div>
                    <span
                      className={`text-sm font-medium ${m.reached ? "text-primary" : "text-muted-foreground"
                        }`}
                    >
                      {m.label}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <Button
            onClick={onLogout}
            variant="outline"
            className="w-full border-2 border-destructive/20 text-destructive hover:bg-destructive/5 rounded-full h-12 font-medium"
          >
            Sign Out
          </Button>
        </motion.div>
      </div>
    </div>
  );
}