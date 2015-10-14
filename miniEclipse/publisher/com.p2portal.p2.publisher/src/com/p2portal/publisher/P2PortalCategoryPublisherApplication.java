package com.p2portal.publisher;

import java.io.File;
import java.io.InputStream;
import java.net.URI;
import java.net.URISyntaxException;
import java.text.MessageFormat;
import java.util.ArrayList;
import java.util.List;
import java.util.Properties;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.eclipse.core.runtime.IStatus;
import org.eclipse.core.runtime.NullProgressMonitor;
import org.eclipse.core.runtime.Status;
import org.eclipse.core.runtime.URIUtil;
import org.eclipse.equinox.app.IApplication;
import org.eclipse.equinox.internal.p2.updatesite.CategoryPublisherApplication;
import org.eclipse.equinox.internal.p2.updatesite.CategoryXMLAction;
import org.eclipse.equinox.p2.core.ProvisionException;
import org.eclipse.equinox.p2.metadata.IInstallableUnit;
import org.eclipse.equinox.p2.publisher.AbstractPublisherApplication;
import org.eclipse.equinox.p2.publisher.IPublisherAction;
import org.eclipse.equinox.p2.publisher.PublisherInfo;
import org.eclipse.equinox.p2.query.IQueryResult;
import org.eclipse.equinox.p2.query.QueryUtil;
import org.eclipse.equinox.p2.repository.metadata.IMetadataRepository;

/**
 * can publish a list of repo
 * and remove old category information
 * 
 *
 */
public class P2PortalCategoryPublisherApplication extends AbstractPublisherApplication {

	private static final String REPOSITORY_SUBFOLDER = "repository.{0}.subfolder";
	private static final String REPOSITORY_ROOT = "repository.{0}.root";
	private Pattern categoryXmlPatterm = Pattern.compile("category\\.(\\d)\\.xmlfile");
	
	private String categoryQualifier = null;
	private URI categoryProperties=null;
	private List<CategoryEntry> entries=new ArrayList<CategoryEntry>();
	
	
	private class CategoryEntry{
		public URI categoryDefinition = null;
		public String[] subFolders = null;
		public File repositoryRoot = null;
	}
	
	public P2PortalCategoryPublisherApplication() {
		// nothing todo
	}

	public Object run(String args[]) throws Exception {
		try {
			info = createPublisherInfo();
			processCommandLineArguments(args, info);
			Object result = publishAll();
			if (result != IApplication.EXIT_OK) {
				for (int i = 0; i < args.length; i++)
					System.out.println(args[i]);
			}
			return result;
		} catch (Exception e) {
			if (e.getMessage() != null)
				System.err.println(e.getMessage());
			else
				e.printStackTrace(System.err);
			throw e;
		}
	}

	/*
	 * Check to see if an existing repository already has the "compressed" flag
	 * set
	 */
	protected Object publishAll() throws ProvisionException {
		try {

			for (CategoryEntry entry : entries) {
				final String[] subFolders = entry.subFolders;
				final File repositoryRoot = entry.repositoryRoot;
				final URI categoryDefinition = entry.categoryDefinition;

				if (subFolders == null || subFolders.length == 0) {
					return new Integer(1);
				}

				for (String path : subFolders) {
					File subRoot = new File(repositoryRoot, path);
					if (!subRoot.exists()) {
						System.err.println("Repository path:" + subRoot + " not exists");
						continue;
					}

					//publish subRoot
					if (isRepository(subRoot)){
						if (publishChild(categoryDefinition, subRoot) != IApplication.EXIT_OK) {
							//break if publish failed
							return new Integer(1);
						}
					}
						
					//publish child of subRoot
					File[] children = subRoot.listFiles();
					for (File child : children) {	
						if (isRepository(child)) {
							if (publishChild(categoryDefinition, child) != IApplication.EXIT_OK) {
								//break if publish failed
								return new Integer(1);
							}

						} else {
							System.err.println("Skippping: " + child + " either not a directory or no content repository found.");
						}
					}

				}
			}
		} catch (ProvisionException e) {
			// do nothing
			e.printStackTrace();
			return new Integer(1);
		}

		return IApplication.EXIT_OK;

	}

	private boolean isRepository(File child) {
		if(!child.isDirectory())
			return false;
		
		return new File(child, "content.xml").exists() || new File(child, "content.jar").exists();
	}

	private Object publishChild(final URI categoryDefinition, File child) throws ProvisionException {
		System.out.println("Publishing category for: " + child);

		// create a category publisher instance
		URI uri = child.toURI();
		CategoryPublisherApplication publisherApplication = new CategoryPublisherApplication() {

			@Override
			protected void initializeRepositories(PublisherInfo publisherInfo) throws ProvisionException {
				// init params, must set append as true
				this.append = true;

				super.initializeRepositories(publisherInfo);

				// remove original category ius
				IMetadataRepository metadataRepository = publisherInfo.getMetadataRepository();
				IQueryResult<IInstallableUnit> queryResult = metadataRepository.query(
						QueryUtil.createIUCategoryQuery(), new NullProgressMonitor());
				metadataRepository.removeInstallableUnits(queryResult.toUnmodifiableSet());

			}

			protected IPublisherAction[] createActions() {
				return new IPublisherAction[] { new CategoryXMLAction(categoryDefinition, categoryQualifier) };
			}
		};

		try {
			// publisherApplication.setArtifactLocation(uri); do not require
			// artifact repository
			publisherApplication.setMetadataLocation(uri);
			publisherApplication.setCompress(this.compress);
			return publisherApplication.run(createPublisherInfo());

		} catch (Exception e) {
			throw new ProvisionException(new Status(IStatus.ERROR, "p2portal.publisher", e.getMessage(), e));
		}

	}

	protected void processParameter(String arg, String parameter, PublisherInfo pinfo) throws URISyntaxException {
		super.processParameter(arg, parameter, pinfo);

		//this.append = true; // Always append, otherwise we will end up with
							// nothing

		if (arg.equalsIgnoreCase("-categoryQualifier")) //$NON-NLS-1$
			categoryQualifier = parameter;

//		if (arg.equalsIgnoreCase("-categoryDefinition")) //$NON-NLS-1$
//			categoryDefinition = URIUtil.fromString(parameter);

		if (arg.equalsIgnoreCase("-repoCategoryDefinition") || arg.equalsIgnoreCase("-rcd")){
			this.categoryProperties = URIUtil.fromString(parameter);
			
			try {
				InputStream in=this.categoryProperties.toURL().openStream();
				Properties prop=new Properties();
				prop.load(in);
				in.close();
				
				Set keys = prop.keySet();
				for (Object keyObj : keys) {
					String key = (String) keyObj;

					Matcher matcher = categoryXmlPatterm.matcher(key);
					if (matcher.matches()) {
						String digit = matcher.group(1);
						CategoryEntry entry = new CategoryEntry();
						entry.categoryDefinition = URIUtil.append(getBase(categoryProperties), prop.getProperty(key));
						entry.repositoryRoot = new File(prop.getProperty(MessageFormat.format(REPOSITORY_ROOT,
								new Object[] { digit })));
						entry.subFolders = prop.getProperty(
								MessageFormat.format(REPOSITORY_SUBFOLDER, new Object[] { digit })).split(",");
						entries.add(entry);
					}

				}
			} catch (Exception e) {
				e.printStackTrace();
			} 
		}
			

	}
	
	private static URI getBase(URI uri) {
		if (uri == null)
			return null;

		String uriString = uri.toString();
		int slashIndex = uriString.lastIndexOf('/');
		if (slashIndex == -1 || slashIndex == (uriString.length() - 1))
			return uri;

		return URI.create(uriString.substring(0, slashIndex + 1));
	}


	@Override
	protected IPublisherAction[] createActions() {
		// do nothing
		return null;
	}

}
