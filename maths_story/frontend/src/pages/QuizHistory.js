import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import {
    Brain,
    ArrowLeft,
    Calendar,
    TrendingUp,
    Filter,
    Clock,
    Target,
    ChevronRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import api from "@/utils/api";
import DarkModeToggle from "@/components/DarkModeToggle";
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
} from "recharts";

export default function QuizHistory({ user, onLogout }) {
    const navigate = useNavigate();
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState({ subject: "", topic: "" });

    useEffect(() => {
        fetchHistory();
    }, [filter]);

    const fetchHistory = async () => {
        try {
            const params = new URLSearchParams();
            if (filter.subject) params.append("subject", filter.subject);
            if (filter.topic) params.append("topic", filter.topic);
            params.append("limit", "50");
            const res = await api.get(`/quiz/history?${params.toString()}`);
            setData(res.data);
        } catch (err) {
            toast.error("Failed to load quiz history");
        } finally {
            setLoading(false);
        }
    };

    const subjects = data
        ? [...new Set(data.results.map((r) => r.subject))]
        : [];

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
                            <span className="text-xl font-serif text-primary">
                                Quiz History
                            </span>
                        </div>
                        <DarkModeToggle />
                    </div>
                </div>
            </header>

            <div className="container mx-auto px-4 py-8">
                {loading ? (
                    <div className="text-center py-20">
                        <div className="inline-block w-8 h-8 border-4 border-accent border-t-transparent rounded-full animate-spin" />
                    </div>
                ) : (
                    <>
                        {/* Score Trend */}
                        {data?.trend && data.trend.length > 1 && (
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="bg-card rounded-2xl border border-border shadow-lg p-6 mb-8"
                            >
                                <div className="flex items-center gap-2 mb-4">
                                    <TrendingUp className="w-5 h-5 text-accent" />
                                    <h2 className="text-xl font-serif text-primary">
                                        Score Trend
                                    </h2>
                                </div>
                                <ResponsiveContainer width="100%" height={220}>
                                    <LineChart data={data.trend}>
                                        <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
                                        <XAxis
                                            dataKey="date"
                                            fontSize={12}
                                            tickFormatter={(v) => v.slice(5)}
                                        />
                                        <YAxis domain={[0, 100]} fontSize={12} />
                                        <Tooltip
                                            contentStyle={{
                                                borderRadius: "12px",
                                                border: "1px solid hsl(var(--border))",
                                                background: "hsl(var(--card))",
                                            }}
                                        />
                                        <Line
                                            type="monotone"
                                            dataKey="score"
                                            stroke="hsl(238, 84%, 62%)"
                                            strokeWidth={2.5}
                                            dot={{ r: 4 }}
                                            activeDot={{ r: 6 }}
                                        />
                                    </LineChart>
                                </ResponsiveContainer>
                            </motion.div>
                        )}

                        {/* Filters */}
                        <div className="flex flex-wrap gap-3 mb-6">
                            <div className="flex items-center gap-2">
                                <Filter className="w-4 h-4 text-muted-foreground" />
                                <select
                                    value={filter.subject}
                                    onChange={(e) =>
                                        setFilter({ ...filter, subject: e.target.value })
                                    }
                                    className="h-9 rounded-lg border border-input bg-background px-3 text-sm"
                                >
                                    <option value="">All Subjects</option>
                                    {subjects.map((s) => (
                                        <option key={s} value={s}>
                                            {s}
                                        </option>
                                    ))}
                                </select>
                            </div>
                            <div className="text-sm text-muted-foreground flex items-center">
                                {data?.total || 0} quiz results
                            </div>
                        </div>

                        {/* Results List */}
                        <div className="space-y-3">
                            {data?.results?.map((result, index) => (
                                <motion.div
                                    key={result.id || index}
                                    initial={{ opacity: 0, x: -20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: index * 0.04 }}
                                    onClick={() => {
                                        sessionStorage.setItem("quizResult", JSON.stringify(result));
                                        navigate(`/results/${result.id}`);
                                    }}
                                    className="bg-card border border-border/40 rounded-xl p-5 flex items-center justify-between hover:shadow-md transition-all cursor-pointer group"
                                >
                                    <div className="flex-1">
                                        <div className="font-medium text-primary">
                                            {result.subject} — {result.topic}
                                        </div>
                                        <div className="flex items-center gap-4 mt-1 text-sm text-muted-foreground">
                                            <span className="flex items-center gap-1">
                                                <Calendar className="w-3.5 h-3.5" />
                                                {new Date(result.created_at).toLocaleDateString()}
                                            </span>
                                            <span className="flex items-center gap-1">
                                                <Clock className="w-3.5 h-3.5" />
                                                {result.avg_time?.toFixed(1)}s avg
                                            </span>
                                            <span className="flex items-center gap-1">
                                                <Target className="w-3.5 h-3.5" />
                                                {result.correct_answers}/{result.total_questions}
                                            </span>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-4">
                                        <div
                                            className={`text-2xl font-serif ${result.score >= 80
                                                    ? "text-success"
                                                    : result.score >= 60
                                                        ? "text-amber-600"
                                                        : "text-destructive"
                                                }`}
                                        >
                                            {result.score.toFixed(0)}%
                                        </div>
                                        <ChevronRight className="w-5 h-5 text-muted-foreground group-hover:text-primary transition-colors" />
                                    </div>
                                </motion.div>
                            ))}
                        </div>

                        {(!data?.results || data.results.length === 0) && (
                            <div className="text-center py-20 text-muted-foreground">
                                <Target className="w-12 h-12 mx-auto mb-4 opacity-30" />
                                <p className="text-lg">No quiz results yet</p>
                                <Button
                                    onClick={() => navigate("/quiz/select")}
                                    className="mt-4 rounded-full"
                                >
                                    Take Your First Quiz
                                </Button>
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    );
}
