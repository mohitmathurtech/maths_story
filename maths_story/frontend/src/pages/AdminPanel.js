import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import {
  Brain,
  ArrowLeft,
  Plus,
  Edit,
  Trash2,
  BookOpen,
  FolderOpen,
  FileText,
  Upload,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import api from "@/utils/api";

export default function AdminPanel({ user, onLogout }) {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("grades");
  const [grades, setGrades] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [topics, setTopics] = useState([]);
  const [subtopics, setSubtopics] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [modalType, setModalType] = useState("");
  const [editingItem, setEditingItem] = useState(null);
  const [selectedSubject, setSelectedSubject] = useState(null);
  const [selectedTopic, setSelectedTopic] = useState(null);
  const [formData, setFormData] = useState({});
  const [uploadFile, setUploadFile] = useState(null);

  useEffect(() => {
    if (user?.role !== "admin") {
      toast.error("Admin access required");
      navigate("/dashboard");
      return;
    }
    loadData();
  }, [activeTab, selectedSubject, selectedTopic]);

  const loadData = async () => {
    setLoading(true);
    try {
      if (activeTab === "grades") {
        const response = await api.get("/admin/grades");
        setGrades(response.data);
      } else if (activeTab === "subjects") {
        const response = await api.get("/admin/subjects");
        setSubjects(response.data);
      } else if (activeTab === "topics") {
        const response = await api.get(
          selectedSubject ? `/admin/topics?subject_id=${selectedSubject}` : "/admin/topics"
        );
        setTopics(response.data);
      } else if (activeTab === "subtopics") {
        const response = await api.get(
          selectedTopic ? `/admin/subtopics?topic_id=${selectedTopic}` : "/admin/subtopics"
        );
        setSubtopics(response.data);
      }
    } catch (error) {
      toast.error("Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  const openModal = (type, item = null) => {
    setModalType(type);
    setEditingItem(item);
    if (item) {
      setFormData(item);
    } else {
      setFormData({});
    }
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setModalType("");
    setEditingItem(null);
    setFormData({});
    setUploadFile(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (modalType === "grade") {
        if (editingItem) {
          await api.put(`/admin/grades/${editingItem.id}`, formData);
          toast.success("Grade updated");
        } else {
          await api.post("/admin/grades", formData);
          toast.success("Grade created");
        }
      } else if (modalType === "subject") {
        if (editingItem) {
          await api.put(`/admin/subjects/${editingItem.id}`, formData);
          toast.success("Subject updated");
        } else {
          await api.post("/admin/subjects", formData);
          toast.success("Subject created");
        }
      } else if (modalType === "topic") {
        const data = { ...formData, subject_id: selectedSubject };
        if (editingItem) {
          await api.put(`/admin/topics/${editingItem.id}`, data);
          toast.success("Topic updated");
        } else {
          await api.post("/admin/topics", data);
          toast.success("Topic created");
        }
      } else if (modalType === "subtopic") {
        const data = { ...formData, topic_id: selectedTopic };
        if (editingItem) {
          await api.put(`/admin/subtopics/${editingItem.id}`, data);
          toast.success("Subtopic updated");
        } else {
          await api.post("/admin/subtopics", data);
          toast.success("Subtopic created");
        }
      }
      closeModal();
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Operation failed");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (type, id) => {
    if (!window.confirm("Are you sure you want to delete this item?")) return;

    setLoading(true);
    try {
      if (type === "grade") {
        await api.delete(`/admin/grades/${id}`);
      } else if (type === "subject") {
        await api.delete(`/admin/subjects/${id}`);
      } else if (type === "topic") {
        await api.delete(`/admin/topics/${id}`);
      } else if (type === "subtopic") {
        await api.delete(`/admin/subtopics/${id}`);
      }
      toast.success("Deleted successfully");
      loadData();
    } catch (error) {
      toast.error("Failed to delete");
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (subtopicId) => {
    if (!uploadFile) {
      toast.error("Please select a PDF file");
      return;
    }

    const formData = new FormData();
    formData.append("file", uploadFile);

    setLoading(true);
    try {
      await api.post(`/admin/subtopics/${subtopicId}/upload-pdf`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      toast.success("PDF uploaded successfully");
      setUploadFile(null);
      loadData();
    } catch (error) {
      toast.error("Failed to upload PDF");
    } finally {
      setLoading(false);
    }
  };

  const handleDeletePDF = async (subtopicId, filename) => {
    if (!window.confirm("Delete this PDF?")) return;

    setLoading(true);
    try {
      await api.delete(`/admin/subtopics/${subtopicId}/pdf/${filename}`);
      toast.success("PDF deleted");
      loadData();
    } catch (error) {
      toast.error("Failed to delete PDF");
    } finally {
      setLoading(false);
    }
  };

  if (user?.role !== "admin") {
    return null;
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-white sticky top-0 z-10">
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
              <span className="text-xl font-serif text-primary">Admin Panel</span>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        {/* Tabs */}
        <div className="flex gap-2 mb-8 border-b border-border overflow-x-auto">
          <button
            onClick={() => setActiveTab("grades")}
            className={`px-6 py-3 font-medium transition-colors whitespace-nowrap ${
              activeTab === "grades"
                ? "border-b-2 border-accent text-accent"
                : "text-muted-foreground hover:text-primary"
            }`}
            data-testid="grades-tab"
          >
            <BookOpen className="w-4 h-4 inline mr-2" />
            Grades
          </button>
          <button
            onClick={() => setActiveTab("subjects")}
            className={`px-6 py-3 font-medium transition-colors whitespace-nowrap ${
              activeTab === "subjects"
                ? "border-b-2 border-accent text-accent"
                : "text-muted-foreground hover:text-primary"
            }`}
            data-testid="subjects-tab"
          >
            <BookOpen className="w-4 h-4 inline mr-2" />
            Subjects
          </button>
          <button
            onClick={() => setActiveTab("topics")}
            className={`px-6 py-3 font-medium transition-colors ${
              activeTab === "topics"
                ? "border-b-2 border-accent text-accent"
                : "text-muted-foreground hover:text-primary"
            }`}
            data-testid="topics-tab"
          >
            <FolderOpen className="w-4 h-4 inline mr-2" />
            Topics
          </button>
          <button
            onClick={() => setActiveTab("subtopics")}
            className={`px-6 py-3 font-medium transition-colors ${
              activeTab === "subtopics"
                ? "border-b-2 border-accent text-accent"
                : "text-muted-foreground hover:text-primary"
            }`}
            data-testid="subtopics-tab"
          >
            <FileText className="w-4 h-4 inline mr-2" />
            Subtopics & PDFs
          </button>
        </div>

        {/* Grades Tab */}
        {activeTab === "grades" && (
          <div>
            <div className="flex justify-between items-center mb-6">
              <div>
                <h2 className="text-2xl font-serif text-primary">Manage Grade Levels</h2>
                <p className="text-sm text-muted-foreground mt-1">
                  Control what grades appear in quiz creation dropdown
                </p>
              </div>
              <Button
                onClick={() => openModal("grade")}
                className="bg-accent text-white rounded-full"
                data-testid="add-grade-btn"
              >
                <Plus className="w-4 h-4 mr-2" />
                Add Grade
              </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {grades.map((grade) => (
                <motion.div
                  key={grade.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-white border border-border rounded-xl p-6 hover:shadow-md transition-shadow"
                  data-testid={`grade-${grade.id}`}
                >
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-lg font-semibold text-primary">{grade.name}</h3>
                    <span className="text-xs text-muted-foreground">Order: {grade.order}</span>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => openModal("grade", grade)}
                      data-testid={`edit-grade-${grade.id}`}
                    >
                      <Edit className="w-4 h-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleDelete("grade", grade.id)}
                      className="text-destructive"
                      data-testid={`delete-grade-${grade.id}`}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </motion.div>
              ))}
            </div>

            {grades.length === 0 && !loading && (
              <div className="text-center py-12 text-muted-foreground">
                <p>No grades added yet. Click "Add Grade" to create one.</p>
              </div>
            )}
          </div>
        )}

        {/* Subjects Tab */}
        {activeTab === "subjects" && (
          <div>
            <div className="flex justify-between items-center mb-6">
              <div>
                <h2 className="text-2xl font-serif text-primary">Manage Subjects</h2>
                <p className="text-sm text-muted-foreground mt-1">
                  Control what subjects appear in quiz creation dropdown
                </p>
              </div>
              <Button
                onClick={() => openModal("subject")}
                className="bg-accent text-white rounded-full"
                data-testid="add-subject-btn"
              >
                <Plus className="w-4 h-4 mr-2" />
                Add Subject
              </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {subjects.map((subject) => (
                <motion.div
                  key={subject.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-white border border-border rounded-xl p-6 hover:shadow-md transition-shadow"
                  data-testid={`subject-${subject.id}`}
                >
                  <h3 className="text-lg font-semibold text-primary mb-2">{subject.name}</h3>
                  <p className="text-sm text-muted-foreground mb-3">
                    {subject.description || "No description"}
                  </p>
                  <div className="flex items-center gap-2 mb-4">
                    <span
                      className={`text-xs px-2 py-1 rounded-full ${
                        subject.is_active
                          ? "bg-success/10 text-success"
                          : "bg-slate-100 text-slate-500"
                      }`}
                    >
                      {subject.is_active ? "Active" : "Inactive"}
                    </span>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => openModal("subject", subject)}
                      data-testid={`edit-subject-${subject.id}`}
                    >
                      <Edit className="w-4 h-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleDelete("subject", subject.id)}
                      className="text-destructive"
                      data-testid={`delete-subject-${subject.id}`}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        )}

        {/* Topics Tab */}
        {activeTab === "topics" && (
          <div>
            <div className="flex justify-between items-center mb-6">
              <div>
                <h2 className="text-2xl font-serif text-primary">Manage Topics</h2>
                <select
                  value={selectedSubject || ""}
                  onChange={(e) => setSelectedSubject(e.target.value)}
                  className="mt-2 px-4 py-2 border border-border rounded-lg"
                  data-testid="subject-filter"
                >
                  <option value="">All Subjects</option>
                  {subjects.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
                </select>
              </div>
              <Button
                onClick={() => openModal("topic")}
                className="bg-accent text-white rounded-full"
                disabled={!selectedSubject}
                data-testid="add-topic-btn"
              >
                <Plus className="w-4 h-4 mr-2" />
                Add Topic
              </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {topics.map((topic) => (
                <motion.div
                  key={topic.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-white border border-border rounded-xl p-6 hover:shadow-md transition-shadow"
                  data-testid={`topic-${topic.id}`}
                >
                  <h3 className="text-lg font-semibold text-primary mb-2">{topic.name}</h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    {topic.description || "No description"}
                  </p>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => openModal("topic", topic)}
                      data-testid={`edit-topic-${topic.id}`}
                    >
                      <Edit className="w-4 h-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleDelete("topic", topic.id)}
                      className="text-destructive"
                      data-testid={`delete-topic-${topic.id}`}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        )}

        {/* Subtopics Tab */}
        {activeTab === "subtopics" && (
          <div>
            <div className="flex justify-between items-center mb-6">
              <div>
                <h2 className="text-2xl font-serif text-primary">Manage Subtopics & Knowledge Base</h2>
                <select
                  value={selectedTopic || ""}
                  onChange={(e) => setSelectedTopic(e.target.value)}
                  className="mt-2 px-4 py-2 border border-border rounded-lg"
                  data-testid="topic-filter"
                >
                  <option value="">All Topics</option>
                  {topics.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.name}
                    </option>
                  ))}
                </select>
              </div>
              <Button
                onClick={() => openModal("subtopic")}
                className="bg-accent text-white rounded-full"
                disabled={!selectedTopic}
                data-testid="add-subtopic-btn"
              >
                <Plus className="w-4 h-4 mr-2" />
                Add Subtopic
              </Button>
            </div>

            <div className="space-y-4">
              {subtopics.map((subtopic) => (
                <motion.div
                  key={subtopic.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-white border border-border rounded-xl p-6"
                  data-testid={`subtopic-${subtopic.id}`}
                >
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="text-lg font-semibold text-primary">{subtopic.name}</h3>
                      <p className="text-sm text-muted-foreground">
                        {subtopic.description || "No description"}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => openModal("subtopic", subtopic)}
                      >
                        <Edit className="w-4 h-4" />
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleDelete("subtopic", subtopic.id)}
                        className="text-destructive"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>

                  {/* PDF Upload Section */}
                  <div className="border-t border-border pt-4">
                    <h4 className="font-medium text-primary mb-3">Knowledge Base PDFs</h4>
                    
                    <div className="flex gap-2 mb-3">
                      <input
                        type="file"
                        accept=".pdf"
                        onChange={(e) => setUploadFile(e.target.files[0])}
                        className="flex-1 text-sm"
                        data-testid={`pdf-upload-${subtopic.id}`}
                      />
                      <Button
                        size="sm"
                        onClick={() => handleFileUpload(subtopic.id)}
                        disabled={!uploadFile || loading}
                        data-testid={`upload-btn-${subtopic.id}`}
                      >
                        <Upload className="w-4 h-4 mr-2" />
                        Upload
                      </Button>
                    </div>

                    {subtopic.knowledge_base_files?.length > 0 && (
                      <div className="space-y-2">
                        {subtopic.knowledge_base_files.map((file, idx) => (
                          <div
                            key={idx}
                            className="flex items-center justify-between bg-slate-50 p-2 rounded"
                          >
                            <span className="text-sm text-primary truncate">{file}</span>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => handleDeletePDF(subtopic.id, file)}
                              className="text-destructive"
                            >
                              <X className="w-4 h-4" />
                            </Button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="bg-white rounded-2xl p-8 max-w-md w-full"
          >
            <h3 className="text-2xl font-serif text-primary mb-6">
              {editingItem ? "Edit" : "Create"} {modalType}
            </h3>
            <form onSubmit={handleSubmit} className="space-y-4">
              {modalType === "grade" && (
                <>
                  <div>
                    <Label>Grade Name *</Label>
                    <Input
                      value={formData.name || ""}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      placeholder="e.g., Grade 10"
                      required
                      data-testid="modal-name-input"
                    />
                  </div>
                  <div>
                    <Label>Order (for sorting) *</Label>
                    <Input
                      type="number"
                      value={formData.order || ""}
                      onChange={(e) => setFormData({ ...formData, order: parseInt(e.target.value) })}
                      placeholder="e.g., 10"
                      required
                      data-testid="modal-order-input"
                    />
                  </div>
                </>
              )}
              
              {(modalType === "subject" || modalType === "topic" || modalType === "subtopic") && (
                <>
                  <div>
                    <Label>Name *</Label>
                    <Input
                      value={formData.name || ""}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      required
                      data-testid="modal-name-input"
                    />
                  </div>
                  <div>
                    <Label>Description</Label>
                    <Input
                      value={formData.description || ""}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      data-testid="modal-description-input"
                    />
                  </div>
                  {modalType === "subject" && (
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        id="is_active"
                        checked={formData.is_active !== false}
                        onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                        className="w-4 h-4"
                        data-testid="modal-active-checkbox"
                      />
                      <Label htmlFor="is_active" className="cursor-pointer">
                        Active (appears in quiz creation)
                      </Label>
                    </div>
                  )}
                </>
              )}
              <div className="flex gap-3">
                <Button type="submit" disabled={loading} className="flex-1" data-testid="modal-submit-btn">
                  {loading ? "Saving..." : "Save"}
                </Button>
                <Button type="button" variant="outline" onClick={closeModal} data-testid="modal-cancel-btn">
                  Cancel
                </Button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </div>
  );
}