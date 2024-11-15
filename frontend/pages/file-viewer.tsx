import React, { useEffect, useState, useCallback } from 'react';
import { fetchItems, fetchReadItemsByAttribute, fetchFile } from '@/utils/api';
import { useRouter } from 'next/router';

interface File {
    name: string | null;
    id: string;
    clean_name: string | null;
    url: string | null;
    s3_key: string | null;
}

const FileViewer: React.FC = () => {
    const [files, setFiles] = useState<File[]>([]);
    const [selectedFile, setSelectedFile] = useState<{ dataUrl: string; fileType: string } | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [pageNumber, setPageNumber] = useState<number | null>(null);
    const router = useRouter();
    const { citation } = router.query;
    const [citationUuid, setCitationUuid] = useState<string>("");

    useEffect(() => {
        if (citation && typeof citation === 'string') {
            setCitationUuid(citation);
        }
    }, [citation]);

    const handleFileClick = useCallback(async (file: File, pageNum?: number) => {
        setIsLoading(true);
        setSelectedFile(null);
        setError(null);
        setPageNumber(pageNum || 1);

        try {
            const { url, fileType } = await fetchFile(file.id);
            setSelectedFile({ dataUrl: url, fileType });
        } catch (error) {
            console.error('Error fetching file data:', error);
            setError('Failed to fetch file. Please try again.');
        } finally {
            setIsLoading(false);
        }
    }, []);
    
    useEffect(() => {
        const fetchFiles = async () => {
            try {
                const response = await fetchReadItemsByAttribute({
                    model: 'file',
                    filters: {}
                });
                setFiles(response);
    
                
                if (citationUuid) {
                    const citation = await fetchItems('chunk', citationUuid);
                    console.log('Citation data:', citation); // Add this for debugging
                    if (citation && citation.id) {
                        handleFileClick({ id: citation.file.id } as File, citation.page_num);
                    }
                }
            } catch (error) {
                console.error('Error fetching files', error);
                setError('Failed to fetch files. Please try again.');
            }
        };
    
        fetchFiles();
    }, [citationUuid, handleFileClick]); 


    const handleDownload = useCallback(() => {
        if (selectedFile) {
            const link = document.createElement('a');
            link.href = selectedFile.dataUrl;
            link.download = 'file'; // You might want to set a proper filename here
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    }, [selectedFile]);

    useEffect(() => {
        return () => {
            if (selectedFile) {
                URL.revokeObjectURL(selectedFile.dataUrl);
            }
        };
    }, [selectedFile]);

    return (
        <div className="file-viewer" style={{ display: 'flex', height: 'calc(100vh - 100px)' }}>
            <div className="file-list" style={{ flex: '0 0 300px', overflowY: 'auto', borderRight: '1px solid #ccc', padding: '20px' }}>
                <h2>Document Set</h2>
                <ul style={{ listStyleType: 'none', padding: 0 }}>
                    {files.map((file) => (
                        <li key={file.id} style={{ marginBottom: '10px' }}>
                            <button
                                onClick={() => handleFileClick(file)}
                                style={{
                                    width: '100%',
                                    textAlign: 'left',
                                    padding: '10px',
                                    border: 'none',
                                    background: '#f0f0f0',
                                    cursor: 'pointer'
                                }}
                            >
                                {file.clean_name || file.name}
                            </button>
                        </li>
                    ))}
                </ul>
            </div>
            <div className="document-viewer" style={{ flex: 1, overflowY: 'auto', padding: '20px' }}>
                {isLoading ? (
                    <div>Loading...</div>
                ) : error ? (
                    <div className="error">{error}</div>
                ) : selectedFile ? (
                    selectedFile.fileType.toLowerCase() === 'application/pdf' ? (
                        <iframe
                            src={`${selectedFile.dataUrl}#view=FitH&navpanes=0${pageNumber ? `&page=${pageNumber}` : ''}`}
                            width="100%"
                            height="100%"
                            style={{ border: 'none' }}
                            title="PDF Viewer"
                        />
                    ) : (
                        <div>
                            <p>This file type cannot be viewed in the browser.</p>
                            <button onClick={handleDownload}>Download File</button>
                        </div>
                    )
                ) : (
                    <div className="no-file-selected">Select a file to view</div>
                )}
            </div>
        </div>
    );
};

export default FileViewer;
