import { NextApiRequest, NextApiResponse } from 'next'
import { filterHeaderForAWSValues } from '@/utils/header'

export default async function handler(
    req: NextApiRequest,
    res: NextApiResponse
): Promise<void> {
    const {
        query: { uuid },
        method,
        headers
    } = req
    switch (method) {
        case 'GET':
            try {
                const request: RequestInit = {
                    method: "GET",
                    headers: {...filterHeaderForAWSValues(headers)} as HeadersInit
                };
                const response = await fetch(process.env.BACKEND_HOST + '/api/get_file/' + uuid, request);
                if (!response.ok) {
                    throw new Error('Failed to get item by uuid');
                }

                // Forward the important headers from the backend response
                const contentType = response.headers.get('content-type');
                const contentDisposition = response.headers.get('content-disposition');
                const xFileType = response.headers.get('x-file-type');

                if (contentType) res.setHeader('Content-Type', contentType);
                if (contentDisposition) res.setHeader('Content-Disposition', contentDisposition);
                if (xFileType) res.setHeader('X-File-Type', xFileType);

                // Stream the response body
                res.status(200);
                const data = await response.arrayBuffer();
                res.send(Buffer.from(data));
            } catch (error) {
                let message
                console.log(error)
                if (error instanceof Error) message = error.message
                res.status(500).send({ error: message })
            }
            break
        default:
            res.setHeader('Allow', ['GET'])
            res.status(405).end(`Method ${method} Not Allowed`)
            break
    }
}
