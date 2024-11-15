import { IncomingHttpHeaders } from "http";

export function filterHeaderForAWSValues(headers: IncomingHttpHeaders) {
    return Object.fromEntries(
        Object.entries(headers).filter(([key, value]) => key.startsWith('x-amzn'))
    );
}
