
# Walkability and Sentiment Analysis Project

## Introduction
This project aims to enhance urban planning and pedestrian experiences through Meso-Scaled/Micro-Scaled Walkability Analysis and BIA-Centered Sentiment Analysis. It combines conventional geographic analysis with AI-driven insights to provide a comprehensive understanding of urban walkability and public sentiment.

Download required dataset: 
[https://drive.google.com/file/d/1BZoXRc6qyod6L7SVUrPF3HZ9Vu_YhxNh/view?usp=sharing]

## Table of Contents
1. [Walkability Analysis](#walkability-analysis)
    - [Introduction](#introduction)
    - [Methodology](#methodology)
    - [Technical Breakdown](#technical-breakdown)
2. [Sentiment Analysis](#sentiment-analysis)
    - [Introduction](#introduction-1)
    - [Methodology](#methodology-1)
    - [Technical Breakdown](#technical-breakdown-1)
3. [Potential Use Cases](#potential-use-cases)

## Walkability Analysis
### Introduction
The conventional Walk Score method often fails to account for pedestrian experiences, leading to misleading scores and potential misallocation of resources. This project introduces a new methodology focusing on the actual pedestrian experience through Meso/Micro-Scaled and image-based analysis.

### Methodology
#### Current Pain Points
- Conventional Walk Score does not consider pedestrian experience.
- Misleading scores lead to less investment in pedestrian infrastructure and green spaces.

#### New Methodology
- Focuses on pedestrian experience using meso/micro-scaled analysis.
- Utilizes Google Maps and image-based analysis.

#### Sample Output
```json
{
    "Walkability Score": 76,
    "Explanations": [
        "Pedestrian Infrastructure: The analyzed area generally has pedestrian walk signals and marked crosswalks, which improve the safety and convenience for pedestrians. However, several construction sites and areas with graffiti were noted, suggesting some disruptions and visual clutter that can detract from the walking experience.",
        "Sidewalk Conditions: Sidewalks are present, but significant sections are poorly maintained with evident road cracks and pavement issues that pose trip hazards. Overgrown grass was observed near the sidewalks, indicating lack of regular maintenance.",
        "Parks and Public Spaces: The area includes a few public parks, but not in every image. The presence and condition of these parks suggest some available green spaces for recreational activities, enhancing walkability slightly.",
        "Transit Stops and Bike Paths: There are public transit stops, which facilitate multimodal transportation options. Designated bike paths are minimal or non-existent in some images, indicating limited infrastructure for cyclists.",
        "Streetlights and Benches: Streetlights are installed, enhancing safety during nighttime; benches and places to sit are scarce, thereby reducing pedestrian convenience, especially for longer walks.",
        "Building Maintenance: Several buildings display signs of poor maintenance, including graffiti. This can impact the perceived safety and aesthetic appeal of the streets.",
        "Buffers and Overhead Coverage: In many areas, buffers between sidewalks and streets are missing or inadequate, increasing pedestrian exposure to vehicular traffic. Tree coverage and awnings providing shade are sparse, resulting in less comfortable walking conditions, especially on hot or rainy days.",
        "Land Use: The predominantly mixed-use nature of the area means there are both residential and commercial activities, which can support a variety of walking purposes but also lead to fluctuating pedestrian traffic volumes and noise levels."
    ]
}
```

### Technical Breakdown
- **AI Processing Model**: Latest GPT-4o (up to May 13, 2024)
- **Image Retrieving**: Google Maps API Street View Image: $7 / 1k Requests
- **Prompt Engineering**: Tailored prompts for detailed analysis

## Sentiment Analysis
### Introduction
Collecting user feedback on urban spaces is essential for efficient urban planning but can be costly and time-consuming. This project leverages Google Maps reviews and GPT-4o to perform sentiment analysis, providing valuable insights for urban planners.

### Methodology
1. Requires input shape files for Road Network and Region of Interest (BIA).
2. Automatically searches for road intersections within the region and retrieves business information around those points.
3. Retrieves reviews for each business and processes sentiment analysis.

#### Sample Output
```
Five Number Summary of Sentiment Scores:
Min: 18
Q1: 74.0
Median: 89.0
Q3: 95.0
Max: 99
```

### Technical Breakdown
- **AI Processing Model**: Latest GPT-4o (up to May 13, 2024)
- **Image Retrieving**: Google Maps API Nearby Search: $17 / 1k Requests
- **Prompt Engineering**: Tailored prompts for detailed analysis

## Potential Use Cases
- **Construction Mitigation**: Provides user-centric information for mitigating daily experience impacts.
- **Tourism**: Designs walking tours based on high walkability scores and positive sentiment analysis.
- **Environmental Sustainability**: Identifies areas needing more trees and green spaces.
- **Real Estate**: Assesses property values based on walkability scores.

## Conclusion
This project combines advanced AI models with comprehensive urban analysis to provide a nuanced understanding of walkability and public sentiment. It offers valuable insights for urban planners, tourism companies, environmental sustainability initiatives, and real estate professionals.

## References
- Bon Woo Koo, Toronto Metropolitan University: [Profile](https://www.torontomu.ca/school-of-urban-and-regional-planning/about/people/faculty/bon-woo-koo/)
- Relevant Publications: [Journal Article](https://journals.sagepub.com/doi/full/10.1177/00139165211014609)
- GitHub Repository: [BonwooKoo/Auto_MAPS](https://github.com/BonwooKoo/Auto_MAPS)
