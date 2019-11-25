<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns="tag:textalign.net,2015:ns" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
   xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:tan="tag:textalign.net,2015:ns"
   xmlns:fn="http://www.w3.org/2005/xpath-functions"
   xmlns:math="http://www.w3.org/2005/xpath-functions/math" exclude-result-prefixes="#all"
   version="2.0">

   <!-- Core functions for TAN-key files. Written principally for Schematron validation, but suitable for general use in other contexts -->

   <xsl:include href="incl/TAN-class-3-functions.xsl"/>
   <xsl:include href="extra/TAN-schema-functions.xsl"/>
   <xsl:include href="incl/TAN-core-functions.xsl"/>

   <xsl:template match="tan:body" mode="core-expansion-terse">
      <xsl:variable name="all-body-iris" select=".//tan:IRI"/>
      <xsl:copy>
         <xsl:copy-of select="@*"/>
         <xsl:apply-templates mode="#current">
            <xsl:with-param name="duplicate-IRIs" select="tan:duplicate-items($all-body-iris)"
               tunnel="yes"/>
            <xsl:with-param name="inherited-affects-elements" select="tan:affects-element"
               tunnel="yes"/>
            <xsl:with-param name="is-reserved"
               select="matches(../@id, '^tag:textalign.net,2015:tan-key:')" tunnel="yes"/>
         </xsl:apply-templates>
      </xsl:copy>
   </xsl:template>
   <xsl:template match="tan:affects-element" mode="core-expansion-terse">
      <xsl:variable name="this-val" select="."/>
      <xsl:copy>
         <xsl:copy-of select="@*"/>
         <xsl:if test="not(. = $TAN-elements-that-take-the-attribute-which/@name)">
            <xsl:variable name="this-fix" as="element()*">
               <xsl:for-each select="$TAN-elements-that-take-the-attribute-which/@name">
                  <xsl:sort select="matches(., $this-val)" order="descending"/>
                  <element affects-element="{.}"/>
               </xsl:for-each>
            </xsl:variable>
            <xsl:copy-of
               select="tan:error('tky03', concat('try: ', string-join($this-fix/@affects-element, ', ')), $this-fix, 'copy-attributes')"
            />
         </xsl:if>
         <xsl:apply-templates mode="#current"/>
      </xsl:copy>
   </xsl:template>
   <xsl:template match="tan:group" mode="core-expansion-terse core-expansion-normal">
      <xsl:param name="inherited-affects-elements" tunnel="yes"/>
      <xsl:variable name="immediate-affects-elements" select="tan:affects-element"/>
      <xsl:variable name="these-affects-elements"
         select="
            if (exists($immediate-affects-elements)) then
               $immediate-affects-elements
            else
               $inherited-affects-elements"/>
      <xsl:copy>
         <xsl:copy-of select="@*"/>
         <xsl:apply-templates mode="#current">
            <xsl:with-param name="inherited-affects-elements" select="$these-affects-elements"
               tunnel="yes"/>
         </xsl:apply-templates>
      </xsl:copy>
   </xsl:template>
   <xsl:template match="tan:item" mode="core-expansion-terse">
      <xsl:param name="is-reserved" as="xs:boolean?" tunnel="yes"/>
      <xsl:param name="inherited-affects-elements" tunnel="yes"/>
      <xsl:variable name="immediate-affects-elements" select="tan:affects-element"/>
      <xsl:variable name="these-affects-elements"
         select="
            if (exists($immediate-affects-elements)) then
               $immediate-affects-elements
            else
               $inherited-affects-elements"/>
      <xsl:variable name="reserved-keyword-doc"
         select="$TAN-keywords[tan:TAN-key/tan:body[tokenize(@affects-element, '\s+') = $these-affects-elements]]"/>
      <xsl:variable name="reserved-keyword-items"
         select="
            if (exists($reserved-keyword-doc)) then
               key('item-via-node-name', $these-affects-elements, $reserved-keyword-doc)
            else
               ()"/>
      <xsl:copy>
         <xsl:copy-of select="@*"/>
         <xsl:if
            test="($is-reserved = true()) and (not(exists(tan:IRI[starts-with(., $TAN-namespace)]))) and (not(exists(tan:token-definition)))">
            <xsl:variable name="this-fix" as="element()">
               <IRI>
                  <xsl:value-of select="$TAN-namespace"/>
               </IRI>
            </xsl:variable>
            <xsl:copy-of select="tan:error('tky04', (), $this-fix, 'prepend-content')"/>
         </xsl:if>
         <xsl:if test="not(every $i in $these-affects-elements satisfies $i = 'verb') and (exists(@object-datatype) or exists(@object-lexical-constraint))">
            <xsl:copy-of select="tan:error('tky05')"/>
         </xsl:if>
         <xsl:apply-templates mode="#current">
            <xsl:with-param name="reserved-keyword-items" select="$reserved-keyword-items"/>
            <xsl:with-param name="inherited-affects-elements" select="$these-affects-elements"
               tunnel="yes"/>
         </xsl:apply-templates>
      </xsl:copy>
   </xsl:template>
   <xsl:template match="tan:IRI[parent::tan:item]" mode="core-expansion-terse">
      <xsl:param name="duplicate-IRIs" tunnel="yes"/>
      <xsl:copy>
         <xsl:copy-of select="@*"/>
         <xsl:if test=". = $duplicate-IRIs">
            <xsl:copy-of select="tan:error('tan09')"/>
         </xsl:if>
         <xsl:apply-templates mode="#current"/>
      </xsl:copy>
   </xsl:template>

   <!-- NORMAL EXPANSION -->

   <xsl:template match="tan:body" mode="core-expansion-normal">
      <xsl:variable name="duplicate-names" as="element()*">
         <xsl:for-each-group select=".//tan:name"
            group-by="(ancestor::tan:*[tan:affects-element])[last()]/tan:affects-element">
            <xsl:for-each-group select="current-group()" group-by=".">
               <xsl:if test="count(current-group()) gt 1">
                  <xsl:copy-of select="current-group()"/>
               </xsl:if>
            </xsl:for-each-group>
         </xsl:for-each-group>
      </xsl:variable>
      <xsl:copy>
         <xsl:copy-of select="@*"/>
         <xsl:apply-templates mode="#current">
            <xsl:with-param name="duplicate-names" select="$duplicate-names" tunnel="yes"/>
         </xsl:apply-templates>
      </xsl:copy>
   </xsl:template>
   <xsl:template match="tan:name" mode="core-expansion-normal">
      <xsl:param name="duplicate-names" tunnel="yes"/>
      <xsl:copy>
         <xsl:copy-of select="@*"/>
         <xsl:if test=". = $duplicate-names">
            <xsl:copy-of select="tan:error('tky02')"/>
         </xsl:if>
         <xsl:apply-templates mode="#current"/>
      </xsl:copy>
   </xsl:template>

</xsl:stylesheet>
