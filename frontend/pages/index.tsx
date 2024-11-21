"use client";

import React, { useEffect, useState } from 'react';
import PieChart from '../components/PieChart';
import { getGateUrl } from '../utils/getGateUrl';
import { fetchUser, fetchReadItemsByAttribute, fetchItems } from '../utils/api';

interface Result {
    answer: string;
    created_datetime: string;
    criterion: Criterion;
    full_text: string;
    id: string;
}

interface Criterion {
    id: string;
    question: string;
    evidence: string;
    category: string;
    gate: string;
}

// Map of gate identifiers to their human-readable format
const gateMap: { [key: string]: string } = {
    'GATE_0': 'Gate 0',
    'GATE_1': 'Gate 1',
    'GATE_2': 'Gate 2',
    'GATE_3': 'Gate 3',
    'GATE_4': 'Gate 4',
    'GATE_5': 'Gate 5'
};

const getBaseName = (name: string): string => name.split('-')[0];

const Summary: React.FC = () => {
    const [chartData, setChartData] = useState<number[]>([]);
    const [chartLabels, setChartLabels] = useState<string[]>([]);
    const [summaryText, setSummaryText] = useState<string>('');
    const [gateUrl, setGateUrl] = useState<string | null>(null);
    const [categories, setCategories] = useState<{ [key: string]: number }>({});
    const [projectDetails, setProjectDetails] = useState<any>(null);
    const [reviewType, setReviewType] = useState<string>('');

    useEffect(() => {
        const fetchData = async () => {
            try {
                console.log('Fetching results...');
                const results = await fetchReadItemsByAttribute({
                    model: 'result',
                    filters: { answer: 'Negative' }
                });
                console.log('Negative results fetched:', results);

                const fetchCriteria = async (result: Result) => {
                    return await fetchItems('criterion', result.criterion.id);
                };

                const criteria = await Promise.all(results.map(fetchCriteria));
                
                // Calculate review type based on unique gates
                const uniqueGates = new Set(criteria.map(criterion => criterion.gate));
                const formattedGates = Array.from(uniqueGates)
                    .map(gate => gateMap[gate] || gate)
                    .sort()
                    .join(', ');
                setReviewType(formattedGates);

                const fetchedCategories = criteria.map(criterion => criterion.category);
                console.log('Criterion fetched:', fetchedCategories);

                const categoryCount: { [key: string]: number } = {};
                fetchedCategories.forEach(category => {
                    categoryCount[category] = (categoryCount[category] || 0) + 1;
                });

                setChartLabels(Object.keys(categoryCount));
                setChartData(Object.values(categoryCount));
                setCategories(categoryCount);

                console.log('Chart labels:', Object.keys(categoryCount));
                console.log('Chart data:', Object.values(categoryCount));

                // Fetching the project details
                console.log('Fetching project details...');
                const projectData = await fetchItems('project');

                console.log('Project details fetched:', projectData);

                if (projectData.length > 0) {
                    setProjectDetails(projectData[0]);
                    setSummaryText(projectData[0].results_summary);
                }

            } catch (error) {
                console.error('Error fetching data:', error);
            }
        };

        fetchData();
    }, []);

    if (!projectDetails) {
        return <div className="summary-card">Loading...</div>;
    }

    return (
        <div>
            <div>
                <br />
                <div className="summary-card" style={{ display: 'flex', alignItems: 'center', marginBottom: '20px', marginTop: '40px' }}>
                    <div style={{ flex: 1 }}>
                        <p>
                            Scout helps you navigate your document set before your review. Please check the details below are correct before continuing.
                            <ul>
                                Project Name:<strong> {projectDetails.name ? getBaseName(projectDetails.name) : projectDetails.name}</strong><br />
                                Review Type:<strong> {reviewType} </strong>
                            
                            </ul>
                            This tool has preprocessed your documents and analysed them against the questions in the {reviewType} workbook. Head to the Results tab to see analysis for each criterion in the gate workbook, click on the links to files to see what evidence has been used to form that conclusion.
                        </p>
                    </div>
                </div>
            </div>

            <div className="summary-card" style={{ display: 'flex', alignItems: 'top', marginBottom: '20px' }}>
                <div style={{ flex: 1 }}>
                    <h2>Overview</h2>
                    <div dangerouslySetInnerHTML={{ __html: summaryText }} />
                </div>
                <div className="chart-container" style={{ flex: 1 }}>
                    <PieChart data={chartData} labels={chartLabels} />
                </div>
            </div>
        </div>
    );
};

export default Summary;