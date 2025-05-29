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
        <xsl:apply-templates/>
    </xsl:template>
    
    
    <xsl:template match="//akn:coverPage">
        <xsl:for-each select=".//text()">
            <xsl:value-of select="normalize-space(.)"/><xsl:text> </xsl:text>
        </xsl:for-each>
    </xsl:template>

    <xsl:template match="//akn:header">
        <xsl:text> 
 |||           
</xsl:text>
        <xsl:for-each select=".//text()">
            <xsl:value-of select="normalize-space(.)"/><xsl:text> </xsl:text>
        </xsl:for-each>
    </xsl:template>

    <xsl:template match="text()|@*" />
    
    
</xsl:stylesheet>