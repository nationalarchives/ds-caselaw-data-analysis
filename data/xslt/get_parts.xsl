<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:html="http://www.w3.org/1999/xhtml" 
    xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn"
    xmlns:akn="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
    exclude-result-prefixes="xs"
    version="3.0">
    <xsl:output method="text" encoding="UTF-8" omit-xml-declaration="yes" indent="no"/>
    <xsl:strip-space elements="*"/>
    
    <xsl:template match="/">
        <xsl:for-each select="//.">
            <xsl:if test="name(.) != '' and (text() != '' or @*)"> 
                <xsl:value-of select="name(.)"/> 
                    <xsl:text>|</xsl:text>
                    <!-- <xsl:value-of select="./@*"/>  -->
                
                    <xsl:if test="not(./@*)">|</xsl:if>
                    <xsl:for-each select="./@*">
                        <xsl:text>|</xsl:text><xsl:value-of select="name(.)"/><xsl:text>=</xsl:text><xsl:value-of select="normalize-space(.)"/>
                    </xsl:for-each>  
                
                    <xsl:text> ||</xsl:text>
                    <xsl:if test="text()">
                        <xsl:value-of select="normalize-space(.)"/>
                    </xsl:if>
            <xsl:text>
</xsl:text>
        </xsl:if>
        </xsl:for-each>
<!--
        <xsl:text> 
            
</xsl:text>
        
        <xsl:for-each select="//text()">
            <xsl:value-of select="."/> 
            <xsl:text> 
</xsl:text>            
        </xsl:for-each>  -->
    </xsl:template>    
    
</xsl:stylesheet>