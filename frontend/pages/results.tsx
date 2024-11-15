import React, { useEffect, useState, useContext, useCallback } from 'react';
import { AgGridReact } from 'ag-grid-react';
import { useRouter } from 'next/router'
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-alpine.css';
import { ColDef, ICellRendererParams } from 'ag-grid-community';
import { Modal, Box, Typography, IconButton, Chip } from '@mui/material';
import { Close as CloseIcon, ThumbUp as ThumbUpIcon, ThumbDown as ThumbDownIcon } from '@mui/icons-material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import HelpIcon from '@mui/icons-material/Help';

import { fetchItems, fetchRelatedItems, rateResponse } from '@/utils/api';
import MagnifyingGlassLoader from '../components/Loader';

interface Rating {
    id: string;
    project: Project;
    result: Result;
    positive_rating: boolean;
    created_datetime: Date;
    updated_datetime: Date | null;
}

interface Criterion {
    id: string;
    category: string;
    created_datetime: Date;
    evidence: string;
    gate: string;
    question: string;
    updated_datetime: Date | null;
}

interface Chunk {
    id: string;
    idx: string;
    page_num: number;
    text: string;
    created_datetime: Date;
    updated_datetime: Date | null;
}

interface Project {
    id: string;
    created_datetime: Date;
    updated_datetime: Date | null;
    name: string;
    results_summary: string | null;
}

interface Result {
    answer: string;
    created_datetime: Date;
    updated_datetime: Date | null;
    criterion: Criterion;
    chunks: Chunk[];
    project: Project;
    ratings: Rating[];
    full_text: string;
    id: string;
}

interface Source {
    chunk_id: string;
    fileName: string;
}

interface TransformedResult {
    Criterion: Criterion;
    Chunks: Chunk[];
    Project: Project;
    Ratings: Rating[];
    Evidence: string;
    Category: string;
    Gate: string;
    Status: string;
    Justification: string;
    Sources: Source[];
    id: string;
}

const style = {
    position: 'absolute' as 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    width: 600,
    bgcolor: 'background.paper',
    borderRadius: '10px',
    boxShadow: 24,
    p: 4,
};

const ResultsTable: React.FC = () => {
    const [results, setResults] = useState<TransformedResult[]>([]);
    const [open, setOpen] = useState(false);
    const [selectedRow, setSelectedRow] = useState<TransformedResult | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [thumbsUpColour, setThumbsUpColour] = useState({color: "none"})
    const [thumbsDownColour, setThumbsDownColour] = useState({color: "none"})
    const router = useRouter();

    useEffect(() => {
        const fetchData = async () => {

            try {
                console.log('Fetching results...');
                const data = await fetchItems('result');
                console.log('Results fetched:', data);

                const transformedResults: TransformedResult[] = await Promise.all(data.map(async (result: Result) => {
                    console.log('Retrieved result:', result);
                    console.log('Retrieved result criterion:', result.criterion);

                    const sources: Source[] = await Promise.all(result.chunks.map(async (chunk: any) => {
                        try {
                            const source = await fetchItems('chunk', chunk.id);
                            console.log('Source object:', source);
                            console.log('Is source undefined?', source === undefined);
                            console.log('Source type:', typeof source);
                            if (source) {
                                console.log('Source attributes:', Object.keys(source));
                                console.log('Source.file:', source.file);
                                if (source.file) {
                                    console.log('Source.file attributes:', Object.keys(source.file));
                                }
                            }

                            return {
                                chunk_id: source?.id || 'Unknown ID',
                                fileName: source?.file?.name || 'Unknown filename'
                            };
                        } catch (error) {
                            console.error('Error fetching or processing chunk:', error);
                            return {
                                chunk_id: chunk.id || 'Unknown ID',
                                fileName: 'Error fetching file name'
                            };
                        }
                    }));


                    const transformedResult: TransformedResult = {
                        Criterion: result.criterion,
                        Evidence: result.criterion.evidence,
                        Category: result.criterion.category,
                        Gate: result.criterion.gate,
                        Status: result.answer,
                        Justification: result.full_text,
                        Sources: sources,
                        id: result.id,
                        Chunks: result.chunks,
                        Project: result.project,
                        Ratings: result.ratings
                    };
                    console.log('Transformed result:', transformedResult);
                    return transformedResult;
                }));

                transformedResults.sort((a, b) => {
                    if (a.Status === 'Negative' && b.Status !== 'Negative') {
                        return -1;
                    }
                    if (a.Status !== 'Negative' && b.Status === 'Negative') {
                        return 1;
                    }
                    return 0;
                });

                console.log('All results transformed and sorted:', transformedResults);
                setResults(transformedResults);
            } catch (error) {
                console.error('Error fetching data:', error);
            } finally {
                setIsLoading(false);
            }
        };

        fetchData();
    }, []);

    const handleCitationClick = (chunk_id: string) => {
        console.log('Citation clicked:', chunk_id);
        router.push({
            pathname: '/file-viewer',
            query: { citation: chunk_id }
        });
    };

    const sourcesFormatter = (params: any) => {
        return params.value.map((source: Source) => (
            <Chip
                key={source.chunk_id}
                label={source.fileName}
                onClick={() => handleCitationClick(source.chunk_id)}
                style={{ margin: '2px', cursor: 'pointer' }}
            />
        ));
    };

    const statusRenderer = (params: ICellRendererParams) => {
        switch (params.value) {
            case 'Positive':
                return <CheckCircleIcon style={{ color: 'green' }} />;
            case 'Neutral':
                return <HelpIcon style={{ color: 'orange' }} />;
            case 'Negative':
                return <ErrorIcon style={{ color: 'red' }} />;
            default:
                return params.value;
        }
    };

    const criterionRenderer = (params: ICellRendererParams) => {
        return params.value.question;
    };

    const columnDefs: ColDef[] = [
        { headerName: 'Criterion', field: 'Criterion', wrapText: true, autoHeight: true, flex: 5, cellRenderer: criterionRenderer, cellStyle: { textAlign: 'left' }, headerClass: 'center-header' },
        { headerName: 'Category', field: 'Category', wrapText: true, autoHeight: true, flex: 1, cellStyle: { textAlign: 'center' }, headerClass: 'center-header' },
        { headerName: 'Status', field: 'Status', wrapText: true, autoHeight: true, flex: 1, cellRenderer: statusRenderer, cellStyle: { textAlign: 'center' }, headerClass: 'center-header' },
        { headerName: 'Sources', field: 'Sources', wrapText: true, autoHeight: true, flex: 3, cellRenderer: sourcesFormatter, cellStyle: { textAlign: 'center' }, headerClass: 'center-header' },
    ];

    const onRowClicked = async (row: any) => {
        setThumbsUpColour({color: ""})
        setThumbsDownColour({color: ""})
        setSelectedRow(row.data);
        const data = await fetchRelatedItems(row.data.id, "result", "rating", true);
        const ratings: Rating[] = await Promise.all(data.map(async (result: Rating) => {
            const transformedRating: Rating = {
                created_datetime: result.created_datetime,
                project: result.project,
                updated_datetime: result.updated_datetime,
                id: result.id,
                result: result.result,
                positive_rating: result.positive_rating
            };
            return transformedRating;
        }));
        if (ratings.length > 0) {
            const sorted_ratings = ratings.sort(function(a,b): any{
                return ((b.updated_datetime ? b.updated_datetime.getTime() : b.created_datetime.getTime()) - (a.updated_datetime ? a.updated_datetime?.getTime() : a.created_datetime.getTime()));
            });
            const latest_rating = sorted_ratings[sorted_ratings.length - 1];
            if (latest_rating.positive_rating) {
                setThumbsUpColour({color: "lightgreen"});
                setThumbsDownColour({color: ""});
            } else {
                setThumbsUpColour({color: "none"});
                setThumbsDownColour({color: "red"});
            }
        }

        setOpen(true);
    };

    const handleClose = () => {
        setOpen(false);
        setSelectedRow(null);
    };

    const getStatusChipColor = (status: string) => {
        switch (status) {
            case 'Positive':
                return 'green';
            case 'Neutral':
                return 'orange';
            case 'Negative':
                return 'red';
            default:
                return 'default';
        }
    };

    const formatEvidence = (evidence: string) => {
        return evidence.split('_').map((item, index) => (
            <React.Fragment key={index}>
                {index > 0 && '• '}
                {item}
                {index > 0 && <br />}
            </React.Fragment>
        ));
    };

    const handleRating = async (goodResponse: boolean) => {
        if (!selectedRow) return;

        try {
            await rateResponse({
                result_id: selectedRow.id,
                good_response: goodResponse,
            });
            console.log(`Rated response ${selectedRow.id} as ${goodResponse ? 'up' : 'down'}`);
            if (goodResponse) {
                setThumbsDownColour({color: ""})
                setThumbsUpColour({color: "lightgreen"})
            } else {
                setThumbsUpColour({color: ""})
                setThumbsDownColour({color: "red"})
            }
        } catch (error) {
            console.error('Error rating response:', error);
        }
    };

    return (
        <div style={{ width: '100%', height: '100vh' }}>
            {isLoading ? (
                <MagnifyingGlassLoader />
            ) : (
                <div className="ag-theme-alpine" style={{ height: 'calc(100% - 64px)', width: '100%' }}>
                    <AgGridReact
                        rowData={results}
                        columnDefs={columnDefs}
                        defaultColDef={{
                            wrapText: true,
                            autoHeight: true,
                        }}
                        onRowClicked={onRowClicked}
                    />
                </div>
            )}
            <Modal open={open} onClose={handleClose}>
                <Box sx={style}>
                    <IconButton
                        aria-label="close"
                        onClick={handleClose}
                        sx={{
                            position: 'absolute',
                            right: 8,
                            top: 8,
                            color: (theme) => theme.palette.grey[500],
                        }}
                    >
                        <CloseIcon />
                    </IconButton>
                    {selectedRow && (
                        <div>
                            <Typography variant="subtitle1"><b>{selectedRow.Criterion.question}</b></Typography>
                            <Typography variant="subtitle1" sx={{ mt: 2 }}>
                                <Box sx={{ display: 'flex', gap: 1 }}>
                                    <Chip label={selectedRow.Status} variant="outlined" style={{ backgroundColor: getStatusChipColor(selectedRow.Status), color: 'white' }} />
                                    <Chip label={selectedRow.Category} variant="outlined" style={{ backgroundColor: 'lightgrey' }} />
                                    <Chip label={selectedRow.Gate} variant="outlined" style={{ backgroundColor: 'lightgrey' }} />
                                </Box>
                            </Typography>

                            <Typography variant="subtitle2" sx={{ mt: 2 }}><b>Evidence Considered</b></Typography>
                            <Typography variant="body1">{formatEvidence(selectedRow.Evidence)}</Typography>
                            <Typography variant="subtitle2" sx={{ mt: 2 }}><b>AI Justification:</b></Typography>
                            <Typography variant="body1">{selectedRow.Justification}</Typography>
                            <Typography variant="subtitle2" sx={{ mt: 2 }}><b>Sources:</b></Typography>
                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
                                {selectedRow.Sources.map((source: Source) => (
                                    <Chip
                                        key={source.chunk_id}
                                        label={source.fileName}
                                        onClick={() => handleCitationClick(source.chunk_id)}
                                        style={{ cursor: 'pointer' }}
                                    />
                                ))}
                            </Box>

                            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                                <IconButton onClick={() => handleRating(true)} aria-label="thumbs up">
                                    <ThumbUpIcon style={thumbsUpColour} />
                                </IconButton>
                                <IconButton onClick={() => handleRating(false)} aria-label="thumbs down">
                                    <ThumbDownIcon style={thumbsDownColour} />
                                </IconButton>
                            </Box>
                        </div>
                    )}
                </Box>
            </Modal>
        </div>
    );
};

export default ResultsTable;
