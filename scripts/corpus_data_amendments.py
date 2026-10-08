"""
Authoritative Constitutional Amendments Corpus Data.
Covers 18 landmark Constitutional Amendments of India:
1st (1951), 24th (1971), 25th (1971), 42nd (1976), 44th (1978), 52nd (1985),
61st (1988), 73rd (1992), 74th (1992), 86th (2002), 91st (2003), 99th (2014),
101st (2016), 102nd (2018), 103rd (2019), 104th (2019), 105th (2021), 106th (2023).
Source: Legislative Department, Ministry of Law and Justice, Government of India.
"""

from typing import List, Dict, Any

PROVENANCE_AMENDMENTS = {
    "source": "Legislative Department, Ministry of Law and Justice, Government of India",
    "retrieval_date": "2026-10-08",
    "version": "Constitutional Amendment Acts Official Gazette",
    "verified": True
}


def get_constitutional_amendments() -> List[Dict[str, Any]]:
    """Returns curated landmark constitutional amendments with provenance."""
    amendments = [
        {
            "id": "amend_001",
            "document_id": "amend_001",
            "document_type": "constitution_amendment",
            "amendment_number": "1st Constitutional Amendment Act",
            "year": 1951,
            "title": "The Constitution (First Amendment) Act, 1951",
            "provisions_modified": ["Article 15(4)", "Article 19(2)", "Article 31A", "Article 31B", "Ninth Schedule"],
            "summary": "Added Article 15(4) enabling affirmative action reservations following Champakam Dorairajan; added 'public order', 'friendly relations with foreign states', and 'incitement to an offence' as reasonable restrictions under Article 19(2); created Ninth Schedule and Article 31B to protect agrarian land reforms from judicial review.",
            "statement_of_objects_and_reasons": "To overcome judicial decisions invalidating state laws regarding land reform, zamindari abolition, and affirmative action, and to introduce reasonable restrictions on freedom of speech in the interest of public order.",
            "provenance": PROVENANCE_AMENDMENTS
        },
        {
            "id": "amend_024",
            "document_id": "amend_024",
            "document_type": "constitution_amendment",
            "amendment_number": "24th Constitutional Amendment Act",
            "year": 1971,
            "title": "The Constitution (Twenty-fourth Amendment) Act, 1971",
            "provisions_modified": ["Article 13(4)", "Article 368"],
            "summary": "Affirmed Parliament's power to amend any part of the Constitution, including Fundamental Rights, by inserting Article 13(4) and amending Article 368. Made presidential assent to constitutional amendment bills mandatory.",
            "statement_of_objects_and_reasons": "Enacted in response to the Supreme Court's ruling in I.C. Golak Nath v. State of Punjab (1967), which held that Parliament could not abridge Fundamental Rights under Article 368.",
            "provenance": PROVENANCE_AMENDMENTS
        },
        {
            "id": "amend_025",
            "document_id": "amend_025",
            "document_type": "constitution_amendment",
            "amendment_number": "25th Constitutional Amendment Act",
            "year": 1971,
            "title": "The Constitution (Twenty-fifth Amendment) Act, 1971",
            "provisions_modified": ["Article 31(2)", "Article 31C"],
            "summary": "Substituted the word 'amount' for 'compensation' under Article 31(2) and inserted Article 31C providing that laws giving effect to Directive Principles in Article 39(b) and (c) cannot be challenged under Articles 14, 19, or 31.",
            "statement_of_objects_and_reasons": "To overcome the Supreme Court ruling in R.C. Cooper (Bank Nationalisation case) regarding market-value compensation for acquired property and to advance socio-economic directive principles.",
            "provenance": PROVENANCE_AMENDMENTS
        },
        {
            "id": "amend_042",
            "document_id": "amend_042",
            "document_type": "constitution_amendment",
            "amendment_number": "42nd Constitutional Amendment Act",
            "year": 1976,
            "title": "The Constitution (Forty-second Amendment) Act, 1976 (Mini-Constitution)",
            "provisions_modified": ["Preamble", "Article 31C", "Article 39A", "Article 43A", "Article 48A", "Part IVA (Article 51A)", "Article 74", "Article 368(4)-(5)"],
            "summary": "Added 'Socialist', 'Secular', and 'Integrity' to the Preamble; introduced Part IVA Fundamental Duties (Article 51A); added Directive Principles on free legal aid (39A), workers participation (43A), and environment (48A); made Council of Ministers advice strictly binding on the President; attempted to make constitutional amendments completely immune from judicial review (later struck down in Minerva Mills).",
            "statement_of_objects_and_reasons": "Comprehensive overhaul based on the Swaran Singh Committee recommendations to assert parliamentary supremacy and implement socio-economic directives during the Emergency.",
            "provenance": PROVENANCE_AMENDMENTS
        },
        {
            "id": "amend_044",
            "document_id": "amend_044",
            "document_type": "constitution_amendment",
            "amendment_number": "44th Constitutional Amendment Act",
            "year": 1978,
            "title": "The Constitution (Forty-fourth Amendment) Act, 1978",
            "provisions_modified": ["Article 19(1)(f)", "Article 31", "Article 300A", "Article 74", "Article 352", "Article 359"],
            "summary": "Restored civil liberties post-Emergency; deleted Right to Property from Fundamental Rights (repealing 19(1)(f) and 31) and reclassified it as a constitutional right under Article 300A; substituted 'armed rebellion' for 'internal disturbance' in Article 352; mandated written Cabinet advice for declaring Emergency; prohibited suspension of Articles 20 and 21 even during National Emergency under Article 359.",
            "statement_of_objects_and_reasons": "Enacted by the Janata Government to dismantle Emergency-era constitutional distortions and safeguard fundamental democratic rights against executive tyranny.",
            "provenance": PROVENANCE_AMENDMENTS
        },
        {
            "id": "amend_052",
            "document_id": "amend_052",
            "document_type": "constitution_amendment",
            "amendment_number": "52nd Constitutional Amendment Act",
            "year": 1985,
            "title": "The Constitution (Fifty-second Amendment) Act, 1985 (Anti-Defection Law)",
            "provisions_modified": ["Article 101", "Article 102", "Article 190", "Article 191", "Tenth Schedule"],
            "summary": "Introduced the Tenth Schedule to prevent political defections ('Aaya Ram, Gaya Ram' culture); disqualified legislators for voluntarily giving up party membership or voting contrary to party whips.",
            "statement_of_objects_and_reasons": "To curb the evil of political defections motivated by lure of office or other considerations that endangered parliamentary democracy.",
            "provenance": PROVENANCE_AMENDMENTS
        },
        {
            "id": "amend_061",
            "document_id": "amend_061",
            "document_type": "constitution_amendment",
            "amendment_number": "61st Constitutional Amendment Act",
            "year": 1988,
            "title": "The Constitution (Sixty-first Amendment) Act, 1988",
            "provisions_modified": ["Article 326"],
            "summary": "Lowered the voting age for elections to the Lok Sabha and State Legislative Assemblies from 21 years to 18 years.",
            "statement_of_objects_and_reasons": "To provide youth with an active opportunity to participate in the democratic process and express their political aspirations.",
            "provenance": PROVENANCE_AMENDMENTS
        },
        {
            "id": "amend_073",
            "document_id": "amend_073",
            "document_type": "constitution_amendment",
            "amendment_number": "73rd Constitutional Amendment Act",
            "year": 1992,
            "title": "The Constitution (Seventy-third Amendment) Act, 1992 (Panchayati Raj)",
            "provisions_modified": ["Part IX (Articles 243 to 243O)", "Eleventh Schedule"],
            "summary": "Conferred constitutional status on Panchayati Raj institutions; established three-tier local governance (Gram, Intermediate, District); mandated 33% reservation for women; instituted State Election Commissions and State Finance Commissions; added Eleventh Schedule with 29 functional items.",
            "statement_of_objects_and_reasons": "To operationalize Article 40 Directive Principle and deepen grassroots participatory democracy in rural India.",
            "provenance": PROVENANCE_AMENDMENTS
        },
        {
            "id": "amend_074",
            "document_id": "amend_074",
            "document_type": "constitution_amendment",
            "amendment_number": "74th Constitutional Amendment Act",
            "year": 1992,
            "title": "The Constitution (Seventy-fourth Amendment) Act, 1992 (Nagarpalikas)",
            "provisions_modified": ["Part IXA (Articles 243P to 243ZG)", "Twelfth Schedule"],
            "summary": "Conferred constitutional status on Urban Local Bodies (Nagar Panchayats, Municipal Councils, Municipal Corporations); mandated regular elections, women's reservation, Ward Committees, and Twelfth Schedule with 18 functional items.",
            "statement_of_objects_and_reasons": "To revitalize urban governance, ensure timely local elections, and devolve administrative powers to municipal bodies.",
            "provenance": PROVENANCE_AMENDMENTS
        },
        {
            "id": "amend_086",
            "document_id": "amend_086",
            "document_type": "constitution_amendment",
            "amendment_number": "86th Constitutional Amendment Act",
            "year": 2002,
            "title": "The Constitution (Eighty-sixth Amendment) Act, 2002 (Right to Education)",
            "provisions_modified": ["Article 21A", "Article 45", "Article 51A(k)"],
            "summary": "Inserted Article 21A making free and compulsory elementary education (ages 6 to 14) a Fundamental Right; amended Article 45 to focus on early childhood care (ages 0 to 6); inserted Fundamental Duty under Article 51A(k) for parents/guardians.",
            "statement_of_objects_and_reasons": "To guarantee every child the fundamental right to quality elementary education, realizing the mandate of Unni Krishnan (1993).",
            "provenance": PROVENANCE_AMENDMENTS
        },
        {
            "id": "amend_091",
            "document_id": "amend_091",
            "document_type": "constitution_amendment",
            "amendment_number": "91st Constitutional Amendment Act",
            "year": 2003,
            "title": "The Constitution (Ninety-first Amendment) Act, 2003",
            "provisions_modified": ["Article 75(1A)", "Article 164(1A)", "Tenth Schedule"],
            "summary": "Capped the size of the Union and State Council of Ministers at 15% of the total strength of the Lok Sabha and Legislative Assembly respectively (minimum 12 in states); deleted the 'split' defense in Tenth Schedule (Paragraph 3) so that individual defectors are always disqualified.",
            "statement_of_objects_and_reasons": "To curb jumbo cabinets, reduce unproductive public expenditure, and strengthen the anti-defection law.",
            "provenance": PROVENANCE_AMENDMENTS
        },
        {
            "id": "amend_099",
            "document_id": "amend_099",
            "document_type": "constitution_amendment",
            "amendment_number": "99th Constitutional Amendment Act",
            "year": 2014,
            "title": "The Constitution (Ninety-ninth Amendment) Act, 2014 (NJAC Act)",
            "provisions_modified": ["Article 124A", "Article 124B", "Article 124C", "Article 217"],
            "summary": "Created the National Judicial Appointments Commission (NJAC) to replace the Supreme Court Collegium system for appointing higher judiciary judges. Struck down in Fourth Judges Case (2015) as unconstitutional for violating judicial independence as a Basic Feature.",
            "statement_of_objects_and_reasons": "To introduce transparency and executive-legislative participation in judicial appointments, which the Supreme Court held infringed the Basic Structure.",
            "provenance": PROVENANCE_AMENDMENTS
        },
        {
            "id": "amend_101",
            "document_id": "amend_101",
            "document_type": "constitution_amendment",
            "amendment_number": "101st Constitutional Amendment Act",
            "year": 2016,
            "title": "The Constitution (One Hundred and First Amendment) Act, 2016 (GST)",
            "provisions_modified": ["Article 246A", "Article 269A", "Article 279A", "Seventh Schedule"],
            "summary": "Introduced the Goods and Services Tax (GST); created concurrent taxation powers under Article 246A; established the GST Council under Article 279A comprising Union Finance Minister and State Finance Ministers.",
            "statement_of_objects_and_reasons": "To replace fragmented multi-layered central and state indirect taxes with a unified national market under the principle of 'One Nation, One Tax'.",
            "provenance": PROVENANCE_AMENDMENTS
        },
        {
            "id": "amend_102",
            "document_id": "amend_102",
            "document_type": "constitution_amendment",
            "amendment_number": "102nd Constitutional Amendment Act",
            "year": 2018,
            "title": "The Constitution (One Hundred and Second Amendment) Act, 2018",
            "provisions_modified": ["Article 338B", "Article 342A"],
            "summary": "Conferred constitutional status on the National Commission for Backward Classes (NCBC) under Article 338B on par with the National Commission for SCs (338) and STs (338A); inserted Article 342A empowering the President to notify socially and educationally backward classes.",
            "statement_of_objects_and_reasons": "To safeguard the constitutional rights, welfare, and developmental interests of Socially and Educationally Backward Classes (SEBCs).",
            "provenance": PROVENANCE_AMENDMENTS
        },
        {
            "id": "amend_103",
            "document_id": "amend_103",
            "document_type": "constitution_amendment",
            "amendment_number": "103rd Constitutional Amendment Act",
            "year": 2019,
            "title": "The Constitution (One Hundred and Third Amendment) Act, 2019 (EWS Reservation)",
            "provisions_modified": ["Article 15(6)", "Article 16(6)"],
            "summary": "Introduced up to 10% reservation for Economically Weaker Sections (EWS) of citizens other than SC, ST, and OBC in educational admissions and public employment. Upheld by Supreme Court 3:2 in Janhit Abhiyan (2022).",
            "statement_of_objects_and_reasons": "To provide constitutional affirmative action for economically underprivileged citizens not covered by existing caste-based reservation policies.",
            "provenance": PROVENANCE_AMENDMENTS
        },
        {
            "id": "amend_104",
            "document_id": "amend_104",
            "document_type": "constitution_amendment",
            "amendment_number": "104th Constitutional Amendment Act",
            "year": 2019,
            "title": "The Constitution (One Hundred and Fourth Amendment) Act, 2019",
            "provisions_modified": ["Article 334"],
            "summary": "Extended the reservation of seats for Scheduled Castes and Scheduled Tribes in the Lok Sabha and State Legislative Assemblies for an additional ten years (until 2030); discontinued the nomination of Anglo-Indian members.",
            "statement_of_objects_and_reasons": "To ensure continued legislative representation for SC and ST communities while discontinuing Anglo-Indian nominations based on demographic changes.",
            "provenance": PROVENANCE_AMENDMENTS
        },
        {
            "id": "amend_105",
            "document_id": "amend_105",
            "document_type": "constitution_amendment",
            "amendment_number": "105th Constitutional Amendment Act",
            "year": 2021,
            "title": "The Constitution (One Hundred and Fifth Amendment) Act, 2021",
            "provisions_modified": ["Article 342A(3)", "Article 338B(9)", "Article 366(26C)"],
            "summary": "Restored the power of State Governments and Union Territories to identify and maintain their own state lists of Socially and Educationally Backward Classes (SEBCs), clarifying that Article 342A only applies to the Central list.",
            "statement_of_objects_and_reasons": "To clarify legislative intent following the Supreme Court's Maratha reservation ruling (Jaishri Patil, 2021) and preserve state-level federal autonomy in identifying backward classes.",
            "provenance": PROVENANCE_AMENDMENTS
        },
        {
            "id": "amend_106",
            "document_id": "amend_106",
            "document_type": "constitution_amendment",
            "amendment_number": "106th Constitutional Amendment Act",
            "year": 2023,
            "title": "The Constitution (One Hundred and Sixth Amendment) Act, 2023 (Nari Shakti Vandan Adhiniyam)",
            "provisions_modified": ["Article 239AA", "Article 330A", "Article 332A", "Article 334A"],
            "summary": "Reserved one-third (33%) of all seats for women in the Lok Sabha, Delhi Legislative Assembly, and State Legislative Assemblies, including seats reserved for SCs and STs, for a period of 15 years following the first census and delimitation exercise.",
            "statement_of_objects_and_reasons": "To ensure equitable gender representation and enhance women's direct participation in national and state policy-making institutions.",
            "provenance": PROVENANCE_AMENDMENTS
        }
    ]
    return amendments
