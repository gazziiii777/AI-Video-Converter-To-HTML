TITLE_PROMPT = '''
Task:
Complete research about [Product Name]. 

Generate a single, readable, SEO-optimized product title for an e-commerce product page about [Product Name] using the provided keywords and phrases.

Algorithm:

1. Normalize Phrases:
- Convert all phrases to lowercase.
- Remove extra spaces.

2. Deduplicate Substrings and Trivial Variations:
- For each phrase, if it is a substring of another phrase (ignoring trivial differences such as spacing, punctuation, or capitalization), remove the shorter or less complete version.

3. Merge Boundary-Variant Phrases with Strict Adherence to Word Order and Semantic Coherence

For any two phrases sharing a long common subsequence, merge them into a single phrase ONLY IF:
Strict Boundary Condition: One phrase starts or ends completely with the other phrase's subsequence, forming a clear boundary (prefix or suffix). The common subsequence must be at the very beginning or the very end of at least one of the phrases.
Non-Overlapping Condition: The shared subsequence does not appear in the middle of both phrases without forming a clear prefix or suffix relationship.
Semantic Coherence Check: The resulting merged phrase must retain semantic coherence and make logical sense. If the merged phrase is nonsensical, do not merge the phrases.
When merging phrases, strictly preserve the exact sequential relationship of words by:
Identifying the longest overlapping sequence of words between the two phrases.
Maintaining a strict left-to-right word order in the merged result.
Positioning unique words from each phrase in their original relative positions without reordering.
Merging should only extend phrases by adding words to the beginning or end. Words should never be rearranged.

Combine Remaining Unique Attributes:
Ensure all remaining unique, meaningful attributes are included in the cleaned list.

Examples:
Merging "version of the core one" + "kit version of the core" must produce "kit version of the core one" (where "kit" precedes the overlap and "one" follows it).
"enclosed 3d printer" and "3d printing community" should not be merged.
"3d printer" and "3d printer community" should be merged to "3d printer community".

4. Prioritize Main Product Name:
- Identify the most complete product name and place it at the start of the Title.

5. Construct the TITLE:
- Add all remaining unique, meaningful attributes in a logical, readable order.
- Use proper punctuation and conjunctions for readability.
- Keep the TITLE concise

Guidelines:
A. Contextual Semantic Integration:
Research the topic online. Rather than mechanical merging, combine phrases based on their semantic meaning
Create logical connections between product attributes, features, and descriptors
Ensure the final title reads naturally with proper flow from product name to attributes

B. Keyword Exclusion 
Omit keywords, if they are not suitable for the intended context.

C. Title Structure and Format:
- Begin with the complete product name as the primary element
- ALWAYS finish with the following statement: "TITLE: Buy or Lease at Top3DShop"
- Use minimal punctuation within the product name portion for readability

D. Standard Title Structure Requirements:
- ALWAYS finish with the following statement: "TITLE: Buy or Lease at Top3DShop"
- Place the complete product name first (including brand)
- Include "Buy or Lease at Top3DShop" as the standard call-to-action suffix
- Maintain proper capitalization (e.g., "CORE" in all caps when referring to the Prusa product)

Output Format:
Only the TITLE. Do not explain your reasoning. Do not reference yourself.

INPUT: 
{titles}
'''

DESC_PROMPT = '''
**Task:**

Complete research about [Product Name]. Generate a single, readable, SEO-optimized meta-description for an e-commerce product page about [Product Name] using the provided keywords and phrases.


**Algorithm:**

1. **Normalize Phrases:**
- Convert all phrases to lowercase.
- Remove extra spaces.

2. **Deduplicate Substrings and Trivial Variations:**
- For each phrase, if it is a substring of another phrase (ignoring trivial differences such as spacing, punctuation, or capitalization), remove the shorter or less complete version.

3. Merge Boundary-Variant Phrases with Strict Adherence to Word Order and Semantic Coherence

For any two phrases sharing a long common subsequence, merge them into a single phrase ONLY IF:
Strict Boundary Condition: One phrase starts or ends completely with the other phrase's subsequence, forming a clear boundary (prefix or suffix). The common subsequence must be at the very beginning or the very end of at least one of the phrases.
Non-Overlapping Condition: The shared subsequence does not appear in the middle of both phrases without forming a clear prefix or suffix relationship.
Semantic Coherence Check: The resulting merged phrase must retain semantic coherence and make logical sense. If the merged phrase is nonsensical, do not merge the phrases.
When merging phrases, strictly preserve the exact sequential relationship of words by:
Identifying the longest overlapping sequence of words between the two phrases.
Maintaining a strict left-to-right word order in the merged result.
Positioning unique words from each phrase in their original relative positions without reordering.
Merging should only extend phrases by adding words to the beginning or end. Words should never be rearranged.

Combine Remaining Unique Attributes:
Ensure all remaining unique, meaningful attributes are included in the cleaned list.

Examples:
Merging "version of the core one" + "kit version of the core" must produce "kit version of the core one" (where "kit" precedes the overlap and "one" follows it).
"enclosed 3d printer" and "3d printing community" should not be merged.
"3d printer" and "3d printer community" should be merged to "3d printer community".

4. **Prioritize Main Product Name:**
- Identify the most complete product name and place it at the start of the meta-description.

5. **Combine Remaining Unique Attributes:**
- Append the brand (if not already in the product name).
- Add all remaining unique, meaningful attributes in a logical, readable order.

6. **Construct the meta-description:**
- Add all remaining unique, meaningful attributes in a logical, readable order.
- Use proper punctuation and conjunctions for readability.
- Keep the meta-description concise
- Research the topic online. Rather than mechanical merging, combine phrases based on their semantic meaning
- Create logical connections between product attributes, features, and descriptors
Ensure the final meta-description reads naturally with proper flow from product name to attributes

Output Format:
Only the meta-description. Do not explain your reasoning. Do not reference yourself

INPUT:
{desc}
'''


H1_PROMPT = '''
Task:
Complete research about [Product Name]. Generate a single, readable, SEO-optimized product heading 1 for an e-commerce product page about [Product Name] using the provided keywords and phrases.

Algorithm:

1. Normalize Phrases:
- Convert all phrases to lowercase.
- Remove extra spaces.

2. Deduplicate Substrings and Trivial Variations:
- For each phrase, if it is a substring of another phrase (ignoring trivial differences such as spacing, punctuation, or capitalization), remove the shorter or less complete version.

3. Merge Boundary-Variant Phrases with Strict Adherence to Word Order and Semantic Coherence

For any two phrases sharing a long common subsequence, merge them into a single phrase ONLY IF:
Strict Boundary Condition: One phrase starts or ends completely with the other phrase's subsequence, forming a clear boundary (prefix or suffix). The common subsequence must be at the very beginning or the very end of at least one of the phrases.
Non-Overlapping Condition: The shared subsequence does not appear in the middle of both phrases without forming a clear prefix or suffix relationship.
Semantic Coherence Check: The resulting merged phrase must retain semantic coherence and make logical sense. If the merged phrase is nonsensical, do not merge the phrases.
When merging phrases, strictly preserve the exact sequential relationship of words by:
Identifying the longest overlapping sequence of words between the two phrases.
Maintaining a strict left-to-right word order in the merged result.
Positioning unique words from each phrase in their original relative positions without reordering.
Merging should only extend phrases by adding words to the beginning or end. Words should never be rearranged.

Combine Remaining Unique Attributes:
Ensure all remaining unique, meaningful attributes are included in the cleaned list.

Examples:
Merging "version of the core one" + "kit version of the core" must produce "kit version of the core one" (where "kit" precedes the overlap and "one" follows it).
"enclosed 3d printer" and "3d printing community" should not be merged.
"3d printer" and "3d printer community" should be merged to "3d printer community".

4. Prioritize Main Product Name:
- Identify the most complete product name and place it at the start of the Heading.

5. Construct the Heading:
- Add all remaining unique, meaningful attributes in a logical, readable order.
- Use proper punctuation and conjunctions for readability.
- Keep the Heading concise

Guidelines:
A. Contextual Semantic Integration:
Research the topic online. Rather than mechanical merging, combine phrases based on their semantic meaning
Create logical connections between product attributes, features, and descriptors
Ensure the final title reads naturally with proper flow from product name to attributes

B. Keyword Exclusion 
Omit keywords, if these are not suitable for the intended context.

C. Title Structure and Format:
- Begin with the complete product name as the primary element
- Use minimal punctuation within the product name portion for readability

D. Standard Title Structure Requirements:
- Place the complete product name first (including brand)
- Ensure the product name portion contains all critical keywords and features
- Maintain proper capitalization (e.g., "CORE" in all caps when referring to the Prusa product)

Output Format:
Only the HEADING. Do not explain your reasoning. Do not reference yourself.

INPUT:
{h1}
'''
