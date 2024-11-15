import React from 'react';
import ReactMarkdown from 'react-markdown';

const PrivacyPolicy: React.FC = () => {
  const markdownContent = `
# Privacy Notice for business correspondence and credentials

This notice sets out how we will use your personal data, and your rights. It is
made under Articles 13 and/or 14 of the UK General Data Protection
Regulation (UK GDPR).

**YOUR DATA**

**PURPOSE**
The purpose(s) for which we are processing your personal data is(are):

- To be used in email correspondence as part of the feedback and
  review process.
- Credentials for access to the Cabinet Office provided Scout Analyser
  platform.

## THE DATA

We will process the following personal data:

- Name (via email)
- Work Email
- Department
- Profession
- IP Address

**LEGAL BASIS FOR PROCESSING**
The legal basis for processing your personal data is:

It is necessary for the purposes of the legitimate interests pursued by the
controller or by a third party. In this case those are providing secure access to
Cabinet Office platforms and applications. As well as enabling you to
participate in electronic communications as part of the feedback on the
process.

## RECIPIENTS

Your personal data will be shared by us with:

- For platform access it will be provided to the provider of the platform.
- Also as your personal data will be stored on our IT infrastructure it will
  also be shared with our data processors who provide email, and
  document management and storage services.

**RETENTION**
Your personal data will be kept by us:

- Platform Credentials - For 6 weeks from the start of the project or until
  you cease to either require access to the platform. At which point the
  data will be deleted from the platform credentials database.

**YOUR RIGHTS**
You have the right to request information about how your personal data are
processed, and to request a copy of that personal data.

You have the right to request that any inaccuracies in your personal data are
rectified without delay.

You have the right to request that any incomplete personal data are
completed, including by means of a supplementary statement.

You have the right to request that your personal data are erased if there is no
longer a justification for them to be processed.

You have the right in certain circumstances (for example, where accuracy is
contested) to request that the processing of your personal data is restricted.

## INTERNATIONAL TRANSFERS

As your personal data is stored on our Corporate IT infrastructure, and shared
with our data processors, it may be transferred and stored securely outside
the UK. Where that is the case it will be subject to equivalent legal protection
through an adequacy decision, reliance on Standard Contractual Clauses, or
reliance on a UK International Data Transfer Agreement.

**COMPLAINTS**
If you consider that your personal data has been misused or mishandled, you
may make a complaint to the Information Commissioner, who is an
independent regulator. The Information Commissioner can be contacted at:
Information Commissioner's Office, Wycliffe House, Water Lane, Wilmslow,
Cheshire, SK9 5AF, or 0303 123 1113, or icocasework@ico.org.uk. Any
complaint to the Information Commissioner is without prejudice to your right to
seek redress through the courts.

**CONTACT DETAILS**

The data controller for your personal data is the Cabinet Office. The contact
details for the data controller are: Cabinet Office, 70 Whitehall, London, SW1A
2AS, or 0207 276 1234, or you can use this webform.

The contact details for the data controller's Data Protection Officer are:
dpo@cabinetoffice.gov.uk.

The Data Protection Officer provides independent advice and monitoring of
Cabinet Office's use of personal information.
`;

  return (
    <div className="markdown-content">
      <ReactMarkdown
        components={{
          p: ({node, ...props}) => <p style={{textAlign: 'left'}} {...props} />,
          h1: ({node, ...props}) => <h1 style={{textAlign: 'left'}} {...props} />,
          h2: ({node, ...props}) => <h2 style={{textAlign: 'left'}} {...props} />,
          li: ({node, ...props}) => <li style={{textAlign: 'left'}} {...props} />
        }}
      >
        {markdownContent}
      </ReactMarkdown>
    </div>
  );
};

export default PrivacyPolicy;
