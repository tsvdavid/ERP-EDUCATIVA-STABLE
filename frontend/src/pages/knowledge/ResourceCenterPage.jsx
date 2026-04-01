import React, { useState, useEffect } from 'react';
import { 
    Library, Search, FileText, ChevronRight, Book, Plus, 
    Edit, Trash2, ArrowLeft, Save, X, Eye, Paperclip, Link as LinkIcon, ExternalLink, Download
} from 'lucide-react';
import { useAuthStore } from '../../context/authStore';
import knowledgeService from '../../services/knowledgeService';

const ResourceCenterPage = () => {
    const { user } = useAuthStore();
    const isAdmin = ['ADMIN', 'RECTOR', 'LOCAL_ADMIN'].includes(user?.role);

    const [categories, setCategories] = useState([]);
    const [articles, setArticles] = useState([]);
    const [loading, setLoading] = useState(true);
    const [view, setView] = useState('grid'); // 'grid', 'category', 'article', 'admin'
    const [selectedItem, setSelectedItem] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');
    
    // Admin States
    const [isEditing, setIsEditing] = useState(false);
    const [isEditingCategory, setIsEditingCategory] = useState(false);
    const [editData, setEditData] = useState({ title: '', content: '', category: '', is_public: true, external_url: '', file: null });
    const [categoryEditData, setCategoryEditData] = useState({ name: '', description: '' });

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [catsData, artsData] = await Promise.all([
                knowledgeService.getCategories(),
                knowledgeService.getArticles()
            ]);
            setCategories(catsData);
            setArticles(artsData);
        } catch (error) {
            console.error("Error fetching knowledge data:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleSaveCategory = async (e) => {
        e.preventDefault();
        try {
            if (categoryEditData.id) {
                await knowledgeService.updateCategory(categoryEditData.id, categoryEditData);
            } else {
                await knowledgeService.createCategory(categoryEditData);
            }
            setIsEditingCategory(false);
            setCategoryEditData({ name: '', description: '' });
            fetchData();
        } catch (error) {
            console.error("Error saving category:", error);
        }
    };

    const handleDeleteCategory = async (id) => {
        if (window.confirm('¿Estás seguro de eliminar esta categoría? Esto podría afectar a los artículos asociados.')) {
            try {
                await knowledgeService.deleteCategory(id);
                fetchData();
            } catch (error) {
                console.error("Error deleting category:", error);
            }
        }
    };

    const handleSaveArticle = async (e) => {
        e.preventDefault();
        try {
            const formData = new FormData();
            formData.append('title', editData.title);
            formData.append('content', editData.content);
            formData.append('category', editData.category);
            formData.append('is_public', editData.is_public);
            if (editData.external_url) formData.append('external_url', editData.external_url);
            
            // Handle file: if it's a new File object, append it. 
            // If it's a string (URL from existing record), we don't need to send it back unless we want to clear it (not handled here yet)
            if (editData.file && typeof editData.file !== 'string') {
                formData.append('file', editData.file);
            }

            if (editData.id) {
                await knowledgeService.updateArticle(editData.id, formData);
            } else {
                await knowledgeService.createArticle(formData);
            }
            setIsEditing(false);
            setEditData({ title: '', content: '', category: '', is_public: true, external_url: '', file: null });
            fetchData();
        } catch (error) {
            console.error("Error saving article:", error);
        }
    };

    const handleDeleteArticle = async (id) => {
        if (window.confirm('¿Estás seguro de eliminar este artículo?')) {
            try {
                await knowledgeService.deleteArticle(id);
                fetchData();
            } catch (error) {
                console.error("Error deleting article:", error);
            }
        }
    };

    const renderHeader = () => (
        <div className="bg-gradient-to-br from-slate-900 to-indigo-950 p-8 lg:p-12 rounded-[2rem] lg:rounded-[3rem] shadow-2xl relative overflow-hidden mb-12 border border-white/5">
            <div className="relative z-10 max-w-2xl">
                <div className="flex items-center gap-4 mb-4">
                    {view !== 'grid' && (
                        <button onClick={() => setView('grid')} className="p-2 bg-white/10 rounded-xl text-white hover:bg-white/20 transition-all">
                            <ArrowLeft size={18} />
                        </button>
                    )}
                    <h1 className="text-2xl lg:text-4xl font-black text-white tracking-tight leading-none">Centro de Recursos</h1>
                </div>
                <p className="text-indigo-100/70 text-sm lg:text-lg mb-8 font-medium">Base de conocimientos. Información oficial a tu alcance.</p>
                
                <div className="relative mb-8">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
                    <input 
                        type="text" 
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        placeholder="Buscar documentos..." 
                        className="w-full bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl py-3 lg:py-4 pl-12 pr-4 text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all font-medium text-sm lg:text-base"
                    />
                </div>

                {isAdmin && (
                    <div className="flex flex-col sm:flex-row gap-3">
                        <button 
                            onClick={() => {
                                setIsEditing(true);
                                setEditData({ title: '', content: '', category: categories[0]?.id || '', is_public: true });
                            }}
                            className="px-6 py-3 bg-white text-indigo-950 rounded-xl lg:rounded-2xl font-bold shadow-xl hover:bg-indigo-50 transition-all flex items-center justify-center gap-2 text-sm"
                        >
                            <Plus size={18} /> Publicar
                        </button>
                        <button 
                            onClick={() => setView('admin-categories')}
                            className="px-6 py-3 bg-indigo-500/20 text-indigo-100 backdrop-blur-md border border-indigo-400/20 rounded-xl lg:rounded-2xl font-bold hover:bg-indigo-500/30 transition-all flex items-center justify-center gap-2 text-sm"
                        >
                            <Library size={18} /> Categorías
                        </button>
                    </div>
                )}
            </div>
            <Library size={300} className="absolute -right-20 -bottom-20 text-white/5 rotate-12 hidden lg:block" />
        </div>
    );

    const renderGridView = () => (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2 space-y-8">
                <h2 className="text-2xl font-bold text-slate-800 flex items-center gap-3">
                    <Book className="text-indigo-600" /> Categorías Principales
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {categories.map(cat => (
                        <div key={cat.id} className="bg-white p-6 lg:p-8 rounded-[1.5rem] lg:rounded-[2.5rem] border border-slate-100 shadow-sm hover:shadow-xl transition-all cursor-pointer group">
                            <div className="w-12 h-12 lg:w-14 lg:h-14 bg-indigo-50 text-indigo-600 rounded-xl lg:rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                                <FileText size={24} className="lg:w-7 lg:h-7" />
                            </div>
                            <h3 className="font-bold text-slate-800 text-lg lg:text-xl mb-1">{cat.name}</h3>
                            <p className="text-xs lg:text-sm text-slate-400 mb-6">{cat.description || 'Consulta documentos oficiales.'}</p>
                            <button className="flex items-center gap-2 text-indigo-600 font-bold text-[10px] lg:text-sm uppercase tracking-wider">
                                Explorar {cat.articles_count || 0} artículos <ChevronRight size={14} />
                            </button>
                        </div>
                    ))}
                    {categories.length === 0 && (
                        <div className="col-span-2 p-12 text-center bg-slate-50 rounded-[2rem] border-2 border-dashed border-slate-200">
                            <p className="text-slate-400 font-medium">No hay categorías configuradas.</p>
                        </div>
                    )}
                </div>
            </div>

            <div className="space-y-8">
                <div className="bg-white rounded-[2.5rem] p-8 border border-slate-100 shadow-sm">
                    <h2 className="text-xl font-bold text-slate-800 mb-8">Artículos Recientes</h2>
                    <div className="space-y-4">
                        {articles.slice(0, 6).map(article => (
                            <div 
                                key={article.id} 
                                onClick={() => {
                                    setSelectedItem(article);
                                    setView('article');
                                }}
                                className="flex items-center justify-between p-4 rounded-2xl hover:bg-slate-50 transition-colors cursor-pointer group border border-transparent hover:border-indigo-100"
                            >
                                    <div className="flex items-center gap-3">
                                        <div className="w-2 h-2 rounded-full bg-indigo-400 group-hover:scale-150 transition-transform"></div>
                                        <div className="flex flex-col">
                                            <span className="font-semibold text-slate-700 group-hover:text-indigo-600 transition-colors">{article.title}</span>
                                            {(article.file || article.external_url) && (
                                                <div className="flex gap-2 mt-1">
                                                    {article.file && <Paperclip size={10} className="text-slate-400" />}
                                                    {article.external_url && <LinkIcon size={10} className="text-slate-400" />}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                {isAdmin ? (
                                    <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                        <button onClick={(e) => {
                                            e.stopPropagation();
                                            setEditData(article);
                                            setIsEditing(true);
                                        }} className="p-2 text-slate-400 hover:text-indigo-600"><Edit size={16}/></button>
                                        <button onClick={(e) => {
                                            e.stopPropagation();
                                            handleDeleteArticle(article.id);
                                        }} className="p-2 text-slate-400 hover:text-red-500"><Trash2 size={16}/></button>
                                    </div>
                                ) : (
                                    <ChevronRight size={16} className="text-slate-300 group-hover:text-indigo-400" />
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );

    const renderArticleView = () => (
        <div className="max-w-4xl mx-auto bg-white rounded-2xl lg:rounded-[3rem] shadow-xl overflow-hidden border border-slate-100 animate-slide-up">
            <div className="p-6 lg:p-12">
                <div className="flex items-center gap-2 text-indigo-600 font-bold text-sm uppercase mb-4 tracking-widest">
                    <FileText size={16} />
                    <span>Artículo Institucional</span>
                </div>
                <h1 className="text-4xl font-black text-slate-800 mb-8 leading-tight">{selectedItem.title}</h1>
                <div className="prose prose-indigo max-w-none text-slate-600 leading-relaxed text-lg mb-12">
                    {selectedItem.content.split('\n').map((para, i) => (
                        <p key={i} className="mb-4">{para}</p>
                    ))}
                </div>

                {(selectedItem.file || selectedItem.external_url) && (
                    <div className="mt-8 pt-8 border-t border-slate-100">
                        <h3 className="text-lg font-bold text-slate-800 mb-6 flex items-center gap-2">
                            <Plus size={20} className="text-indigo-600" /> Material de Apoyo
                        </h3>
                        <div className="flex flex-wrap gap-4">
                            {selectedItem.file && (
                                <a 
                                    href={selectedItem.file} 
                                    target="_blank" 
                                    rel="noopener noreferrer"
                                    className="flex items-center gap-3 px-6 py-4 bg-indigo-50 text-indigo-700 rounded-2xl hover:bg-indigo-100 transition-all font-bold border border-indigo-100"
                                >
                                    <Download size={18} /> Descargar PDF / Archivo
                                </a>
                            )}
                            {selectedItem.external_url && (
                                <a 
                                    href={selectedItem.external_url} 
                                    target="_blank" 
                                    rel="noopener noreferrer"
                                    className="flex items-center gap-3 px-6 py-4 bg-slate-50 text-slate-700 rounded-2xl hover:bg-slate-100 transition-all font-bold border border-slate-100"
                                >
                                    <ExternalLink size={18} /> Ver Enlace Externo
                                </a>
                            )}
                        </div>
                    </div>
                )}
            </div>
            <div className="bg-slate-50 p-8 border-t border-slate-100 flex items-center justify-between">
                <p className="text-slate-400 text-sm font-medium">Última actualización: {new Date(selectedItem.updated_at).toLocaleDateString()}</p>
                <button 
                    onClick={() => setView('grid')}
                    className="flex items-center gap-2 text-slate-600 font-bold hover:text-indigo-600 transition-colors"
                >
                    <ArrowLeft size={18} /> Volver al Repositorio
                </button>
            </div>
        </div>
    );

    const renderEditor = () => (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-md z-[100] flex items-center justify-center p-6 sm:p-12">
            <div className="bg-white w-full max-w-4xl rounded-[3rem] shadow-2xl overflow-hidden animate-zoom-in">
                <div className="p-8 sm:p-12">
                    <div className="flex items-center justify-between mb-8">
                        <div>
                            <h2 className="text-3xl font-black text-slate-800 tracking-tight">
                                {editData.id ? 'Editar Artículo' : 'Nuevo Artículo'}
                            </h2>
                            <p className="text-slate-400 font-medium">Crea contenido práctico para la comunidad educativa.</p>
                        </div>
                        <button onClick={() => setIsEditing(false)} className="p-3 bg-slate-50 text-slate-400 rounded-2xl hover:bg-slate-100 transition-all">
                            <X size={24} />
                        </button>
                    </div>

                    <form onSubmit={handleSaveArticle} className="space-y-6">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="space-y-2">
                                <label className="text-sm font-bold text-slate-700 ml-2">Título del Artículo</label>
                                <input 
                                    type="text"
                                    required
                                    value={editData.title}
                                    onChange={e => setEditData({...editData, title: e.target.value})}
                                    className="w-full bg-slate-50 border-2 border-transparent focus:border-indigo-100 focus:bg-white rounded-2xl p-4 outline-none transition-all font-semibold"
                                    placeholder="Ej: Misión Institucional"
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-bold text-slate-700 ml-2">Categoría</label>
                                <select 
                                    required
                                    value={editData.category}
                                    onChange={e => setEditData({...editData, category: e.target.value})}
                                    className="w-full bg-slate-50 border-2 border-transparent focus:border-indigo-100 focus:bg-white rounded-2xl p-4 outline-none transition-all font-semibold appearance-none"
                                >
                                    <option value="">Selecciona una categoría</option>
                                    {categories.map(cat => (
                                        <option key={cat.id} value={cat.id}>{cat.name}</option>
                                    ))}
                                </select>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-bold text-slate-700 ml-2">Contenido (Soporta múltiples líneas)</label>
                            <textarea 
                                required
                                value={editData.content}
                                onChange={e => setEditData({...editData, content: e.target.value})}
                                rows={6}
                                className="w-full bg-slate-50 border-2 border-transparent focus:border-indigo-100 focus:bg-white rounded-2xl p-6 outline-none transition-all font-medium resize-none"
                                placeholder="Escribe aquí toda la información detallada..."
                            />
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="space-y-2">
                                <label className="text-sm font-bold text-slate-700 ml-2">Archivo / PDF de Apoyo</label>
                                <div className="relative">
                                    <input 
                                        type="file"
                                        onChange={e => setEditData({...editData, file: e.target.files[0]})}
                                        className="w-full bg-slate-50 border-2 border-dashed border-slate-200 rounded-2xl p-4 outline-none transition-all font-semibold text-sm cursor-pointer hover:border-indigo-300"
                                    />
                                    {editData.file && typeof editData.file === 'string' && (
                                        <div className="mt-2 text-xs text-indigo-600 font-bold ml-2 flex items-center gap-1">
                                            <Paperclip size={12} /> Archivo actual: {editData.file.split('/').pop()}
                                        </div>
                                    )}
                                </div>
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-bold text-slate-700 ml-2">Enlace Externo (URL)</label>
                                <div className="relative">
                                    <LinkIcon className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                                    <input 
                                        type="url"
                                        value={editData.external_url}
                                        onChange={e => setEditData({...editData, external_url: e.target.value})}
                                        className="w-full bg-slate-50 border-2 border-transparent focus:border-indigo-100 focus:bg-white rounded-2xl py-4 pl-12 pr-4 outline-none transition-all font-semibold"
                                        placeholder="https://ejemplo.com/recurso"
                                    />
                                </div>
                            </div>
                        </div>

                        <div className="flex items-center justify-between pt-4">
                            <label className="flex items-center gap-3 cursor-pointer group">
                                <input 
                                    type="checkbox" 
                                    checked={editData.is_public}
                                    onChange={e => setEditData({...editData, is_public: e.target.checked})}
                                    className="w-6 h-6 rounded-lg text-indigo-600 border-2 border-slate-200 focus:ring-0 cursor-pointer" 
                                />
                                <span className="font-bold text-slate-600 group-hover:text-slate-800 transition-colors">Visible para todos</span>
                            </label>
                            <div className="flex items-center gap-4">
                                <button 
                                    type="button"
                                    onClick={() => setIsEditing(false)}
                                    className="px-8 py-4 bg-slate-50 text-slate-500 rounded-[1.5rem] font-bold hover:bg-slate-100 transition-all"
                                >
                                    Cancelar
                                </button>
                                <button 
                                    type="submit"
                                    className="px-10 py-4 bg-indigo-600 text-white rounded-[1.5rem] font-black shadow-lg shadow-indigo-200 hover:bg-indigo-700 transition-all flex items-center gap-3"
                                >
                                    <Save size={20} />
                                    Guardar Publicación
                                </button>
                            </div>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );

    const renderCategoriesAdmin = () => (
        <div className="space-y-8 animate-fade-in">
            <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold text-slate-800 flex items-center gap-3">
                    <Library className="text-indigo-600" /> Gestión de Categorías
                </h2>
                <button 
                    onClick={() => {
                        setIsEditingCategory(true);
                        setCategoryEditData({ name: '', description: '' });
                    }}
                    className="px-6 py-3 bg-indigo-600 text-white rounded-2xl font-bold shadow-lg shadow-indigo-200 hover:bg-indigo-700 transition-all flex items-center gap-2"
                >
                    <Plus size={20} /> Nueva Categoría
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {categories.map(cat => (
                    <div key={cat.id} className="bg-white p-6 rounded-[2rem] border border-slate-100 shadow-sm flex flex-col justify-between">
                        <div>
                            <h3 className="font-bold text-slate-800 text-lg mb-2">{cat.name}</h3>
                            <p className="text-sm text-slate-400 mb-4">{cat.description || 'Sin descripción.'}</p>
                        </div>
                        <div className="flex items-center justify-end gap-2 border-t border-slate-50 pt-4">
                            <button 
                                onClick={() => {
                                    setCategoryEditData(cat);
                                    setIsEditingCategory(true);
                                }}
                                className="p-2 text-slate-400 hover:text-indigo-600 transition-colors"
                            >
                                <Edit size={18} />
                            </button>
                            <button 
                                onClick={() => handleDeleteCategory(cat.id)}
                                className="p-2 text-slate-400 hover:text-red-500 transition-colors"
                            >
                                <Trash2 size={18} />
                            </button>
                        </div>
                    </div>
                ))}
            </div>

            {isEditingCategory && (
                <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-md z-[110] flex items-center justify-center p-6">
                    <div className="bg-white w-full max-w-lg rounded-[2.5rem] shadow-2xl overflow-hidden animate-zoom-in">
                        <div className="p-8">
                            <div className="flex items-center justify-between mb-6">
                                <h3 className="text-2xl font-bold text-slate-800">
                                    {categoryEditData.id ? 'Editar Categoría' : 'Nueva Categoría'}
                                </h3>
                                <button onClick={() => setIsEditingCategory(false)} className="p-2 text-slate-400 hover:bg-slate-50 rounded-xl transition-all">
                                    <X size={20} />
                                </button>
                            </div>
                            <form onSubmit={handleSaveCategory} className="space-y-4">
                                <div className="space-y-1">
                                    <label className="text-xs font-bold text-slate-500 ml-1">Nombre</label>
                                    <input 
                                        type="text"
                                        required
                                        value={categoryEditData.name}
                                        onChange={e => setCategoryEditData({...categoryEditData, name: e.target.value})}
                                        className="w-full bg-slate-50 border-2 border-transparent focus:border-indigo-100 focus:bg-white rounded-xl p-3 outline-none transition-all font-semibold"
                                        placeholder="Ej: Trámites Legales"
                                    />
                                </div>
                                <div className="space-y-1">
                                    <label className="text-xs font-bold text-slate-500 ml-1">Descripción</label>
                                    <textarea 
                                        value={categoryEditData.description}
                                        onChange={e => setCategoryEditData({...categoryEditData, description: e.target.value})}
                                        className="w-full bg-slate-50 border-2 border-transparent focus:border-indigo-100 focus:bg-white rounded-xl p-3 outline-none transition-all font-medium resize-none"
                                        rows={3}
                                        placeholder="Breve descripción de la categoría..."
                                    />
                                </div>
                                <div className="flex justify-end gap-3 pt-4">
                                    <button 
                                        type="button"
                                        onClick={() => setIsEditingCategory(false)}
                                        className="px-6 py-3 text-slate-500 font-bold"
                                    >
                                        Cancelar
                                    </button>
                                    <button 
                                        type="submit"
                                        className="px-8 py-3 bg-indigo-600 text-white rounded-xl font-bold shadow-lg hover:bg-indigo-700 transition-all"
                                    >
                                        Guardar
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );

    if (loading) return <div className="flex items-center justify-center h-64 text-slate-400 font-bold">Iniciando Centro de Recursos...</div>;

    return (
        <div className="space-y-4 animate-fade-in pb-20">
            {renderHeader()}
            {view === 'grid' && renderGridView()}
            {view === 'article' && renderArticleView()}
            {view === 'admin-categories' && renderCategoriesAdmin()}
            {isEditing && renderEditor()}
        </div>
    );
};

export default ResourceCenterPage;
